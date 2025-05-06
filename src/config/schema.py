from typing import Sequence

from config import get_db_config
import jieba
from mcp.types import TextContent
from sklearn.feature_extraction.text import TfidfVectorizer
import mysql.connector
from neo4j import GraphDatabase

from config.dbconfig import get_neo4j_config

from wordprocess.chinese_wordnet import get_synonyms, is_semantically_similar


def init_neo4j_graph():
    """
    将 MySQL schema 导入 Neo4j，构建图模型。
    """



    print("Extracting MySQL schema...")
    tables, columns, foreign_keys = extract_mysql_schema()
    print("Finished extracting MySQL schema")
    print("Building Neo4j graph model...")
    build_neo4j_graph(tables, columns, foreign_keys)
    print("Finished building Neo4j graph model")



# ==================== Step 1: 解析 MySQL Schema ====================
def extract_mysql_schema():
    """
    提取 MySQL 数据库的表、字段、注释和外键关系。
    """
    mysql_config = get_db_config()
    connection = mysql.connector.connect(**{k: v for k, v in mysql_config.items() if k != "role"})
    cursor = connection.cursor(dictionary=True)

    # 获取表注释
    cursor.execute("""
        SELECT TABLE_NAME, TABLE_COMMENT 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = %s ;
    """, (mysql_config['database'],))
    tables = cursor.fetchall()

    # 获取字段注释
    cursor.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, COLUMN_COMMENT, DATA_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND COLUMN_NAME NOT IN ('CREATE_USER','CREATE_TIME','UPDATE_USER','UPDATE_TIME')
    """, (mysql_config['database'],))
    columns = cursor.fetchall()

    # 获取外键关系
    cursor.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL;
    """, (mysql_config['database'],))
    foreign_keys = cursor.fetchall()

    cursor.close()
    connection.close()

    for table in tables:
        if table['TABLE_COMMENT']:
            jieba.add_word(table['TABLE_COMMENT'].removesuffix('表').removesuffix('信息'))

    for column in columns:
        if column['COLUMN_COMMENT']:
            jieba.add_word(column['COLUMN_COMMENT'])

    return tables, columns, foreign_keys


# ==================== Step 2: 构建 Neo4j 图模型 ====================
def build_neo4j_graph(tables, columns, foreign_keys):
    """
    将 MySQL schema 导入 Neo4j，构建图模型。
    """

    neo4j_config = get_neo4j_config()

    driver = GraphDatabase.driver(neo4j_config['neo4j_uri'], auth=(neo4j_config['neo4j_user'], neo4j_config['neo4j_password']))

    with driver.session() as session:
        # 清空现有数据（可选）
        # session.run("MATCH (n) DETACH DELETE n")

        # 创建表节点（包括表注释）
        for table in tables:
            table_name = table['TABLE_NAME']
            table_comment = table['TABLE_COMMENT']

            session.run("""
                MERGE (table:Table {name: $table_name})
                ON CREATE SET table.comment = $table_comment
            """, table_name=table_name, table_comment=table_comment)

        # 创建字段节点（包括字段注释）
        for column in columns:
            table_name = column['TABLE_NAME']
            field_name = column['COLUMN_NAME']
            field_comment = column['COLUMN_COMMENT']
            data_type = column['DATA_TYPE']

            session.run("""
                MERGE (field:Field {name: $field_name})
                ON CREATE SET field.comment = $field_comment, field.data_type = $data_type
                WITH field
                MATCH (table:Table {name: $table_name})
                MERGE (table)-[:HAS_FIELD]->(field)
            """, table_name=table_name, field_name=field_name, field_comment=field_comment, data_type=data_type)

        # 创建外键关系
        for fk in foreign_keys:
            table_name = fk['TABLE_NAME']
            column_name = fk['COLUMN_NAME']
            referenced_table = fk['REFERENCED_TABLE_NAME']
            referenced_column = fk['REFERENCED_COLUMN_NAME']

            session.run("""
                MATCH (table1:Table {name: $table_name}), (table2:Table {name: $referenced_table})
                MERGE (table1)-[:FOREIGN_KEY {column: $column_name, references: $referenced_column}]->(table2)
            """, table_name=table_name, referenced_table=referenced_table,
                        column_name=column_name, referenced_column=referenced_column)

    driver.close()


def extract_keywords(query):
    """
    提取用户查询中的关键字，并与 Neo4j 中的 schema（包括表名、字段名和注释）进行匹配。
    :param query: 用户的自然语言查询
    :return: 相关关键字列表
    """
    # Step 1: 使用 jieba 分词并提取名词
    words = jieba.lcut(query)
    noun_words = [word for word in words if len(word) > 1]  # 过滤掉单字词

    # Step 2: 使用 TF-IDF 提取关键词
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([query])
    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = tfidf_matrix.toarray()[0]

    # 按 TF-IDF 分数排序，提取前 N 个关键词
    top_n = 5  # 提取前 5 个关键词
    top_keywords = [feature_names[i] for i in tfidf_scores.argsort()[-top_n:][::-1]]

    # 合并分词结果和 TF-IDF 关键词
    keywords = list(set(noun_words + top_keywords))

    print('拆分关键字：')
    print(keywords)

    # Step 3: 从 Neo4j 获取表名、字段名和注释
    relevant_keywords = []
    neo4j_config = get_neo4j_config()
    driver = GraphDatabase.driver(uri = neo4j_config['neo4j_uri'], auth=(neo4j_config['neo4j_user'], neo4j_config['neo4j_password']))
    with driver.session() as session:
        result = session.run("""
            MATCH (t:Table)-[:HAS_FIELD]->(f:Field)
            RETURN t.name AS table_name, t.comment AS table_comment, 
                   f.name AS field_name, f.comment AS field_comment
        """)
        schema_terms = []
        for record in result:
            table_name = record["table_name"]
            table_comment = record["table_comment"] or ""
            field_name = record["field_name"]
            field_comment = record["field_comment"] or ""

            # 添加表名和字段名
            schema_terms.append((table_name, "table", table_comment))
            schema_terms.append((field_name, "field", field_comment))

        # Step 4: 匹配关键词
        matched_terms = []
        for keyword in keywords:
            for term, term_type, comment in schema_terms:
                # 匹配表名/字段名或注释
                keyword_synonyms = get_synonyms(keyword.lower())
                if (keyword.lower() in term.lower() or
                        any(keyword.lower() == word.strip().lower() for word in comment.split(',')) or
                        any(word.strip().lower() in keyword_synonyms for word in comment.split(',')) or
                        any(is_semantically_similar(keyword, word.strip()) for word in comment.split(','))):
                    matched_terms.append((term, term_type, comment))

        if matched_terms:
            matched_terms = list(set(matched_terms))
        print('匹配到的关键字：')
        print(matched_terms)

        # Step 5: 去重并按优先级排序
        unique_terms = {}
        for term, term_type, comment in matched_terms:
            if term not in unique_terms:
                # 赋予不同权重：表名 > 字段名 > 注释
                weight = 3 if term_type == "table" else 2 if term_type == "field" else 1
                unique_terms[term] = (weight, comment)

        # 按权重排序，返回结果
        sorted_terms = sorted(unique_terms.items(), key=lambda x: x[1][0], reverse=True)
        relevant_keywords = [term for term, _ in sorted_terms]

    return relevant_keywords

def generate_table_info(keywords):
    """
    根据关键字从 Neo4j 中提取相关表、字段以及外键关系信息。
    :param keywords: 自然语言查询
    :return: 格式化的表、字段和外键关系信息字符串
    """

    neo4j_config = get_neo4j_config()
    driver = GraphDatabase.driver(uri=neo4j_config['neo4j_uri'],
                                  auth=(neo4j_config['neo4j_user'], neo4j_config['neo4j_password']))


    table_info = "Available Tables and Columns:\n"
    with driver.session() as session:
        # 查询相关表和字段
        result = session.run("""
            MATCH (t:Table)-[:HAS_FIELD]->(f:Field)
            WHERE ANY(keyword IN $keywords WHERE 
                toLower(t.name) CONTAINS toLower(keyword) OR 
                toLower(f.name) CONTAINS toLower(keyword) OR 
                toLower(t.comment) CONTAINS toLower(keyword) OR 
                toLower(f.comment) CONTAINS toLower(keyword))
            RETURN DISTINCT t.name AS table_name, t.comment AS table_comment, f.data_type AS data_type,
                   f.name AS field_name, f.comment AS field_comment
            ORDER BY t.name, f.name
        """, keywords=keywords)

        current_table = None
        for record in result:
            table_name = record["table_name"]
            table_comment = record["table_comment"] or ""
            field_name = record["field_name"]
            field_comment = record["field_comment"] or ""
            field_type = record["data_type"]

            # 如果切换到新的表，添加表信息
            if table_name != current_table:
                table_info += f"\nTable: {table_name} ({table_comment})\n"
                current_table = table_name

            # 添加字段信息
            table_info += f"  - {field_name} ({field_type}, {field_comment})\n"

        # 查询相关外键关系
        fk_result = session.run("""
            MATCH (table1:Table)-[r:FOREIGN_KEY]->(table2:Table)
            WHERE ANY(keyword IN $keywords WHERE 
                toLower(table1.name) CONTAINS toLower(keyword) OR 
                toLower(table2.name) CONTAINS toLower(keyword))
            RETURN DISTINCT table1.name AS from_table, r.column AS from_column, 
                   table2.name AS to_table, r.references AS to_column
        """, keywords=keywords)

        # 添加外键关系信息
        if fk_result.peek():
            table_info += "\nForeign Key Relationships:\n"
            for record in fk_result:
                from_table = record["from_table"]
                from_column = record["from_column"]
                to_table = record["to_table"]
                to_column = record["to_column"]
                table_info += (
                    f"  - Table {from_table}.{from_column} references "
                    f"{to_table}.{to_column}\n"
                )

    return table_info.strip()


async def get_schema(query) -> Sequence[TextContent]:
    relevant_keywords = extract_keywords(query)
    table_info = generate_table_info(relevant_keywords)
    print('获取到的schema：')
    print(table_info)
    relevant_schema = [TextContent(type="text", text = table_info)]
    return relevant_schema