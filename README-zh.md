# mcp_mysql_server

## 介绍
- 新增 支持 STDIO 方式 与 SSE 方式
- 新增 支持多sql执行，以“;”分隔。 
- 新增 根据表注释可以查询出对于的数据库表名，表字段
- 新增 中文字段转拼音


## 使用说明

### STDIO 方式 
- 使用 src/studio_mcp/operatemysql.py 

将以下内容添加到你的 mcp client 工具中，例如cursor、cline等

mcp json 如下
```
{
  "mcpServers": {
      "operateMysql": {
        "isActive": true,
        "name": "operateMysql",
        "command": "uv",
        "args": [
          "--directory",
          "G:\\python\\mysql_mcp\\src\\studio_mcp",  # 这里需要替换为你的项目路径
          "run",
          "operatemysql.py"
        ],
        "env": {
          "MYSQL_HOST": "192.168.xxx.xxx",
          "MYSQL_PORT": "3306",
          "MYSQL_USER": "root",
          "MYSQL_PASSWORD": "root",
          "MYSQL_DATABASE": "a_llm"
       }
    }
  }
}    
```
### SSE 方式
- 使用 src/sse_mcp/operatemysql.py
- 使用 uv 启动服务

将以下内容添加到你的 mcp client 工具中，例如cursor、cline等

mcp json 如下
````
{
  "mcpServers": {
    "operateMysql": {
      "name": "operateMysql",
      "description": "",
      "isActive": true,
      "baseUrl": "http://localhost:9000/sse"
    }
  }
}
````

修改.env 文件内容,将数据库连接信息修改为你的数据库连接信息
```
# MySQL数据库配置
MYSQL_HOST=192.168.xxx.xxx
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=a_llm
```

启动命令
```
uv run operatemysql.py
```

## 示例
prompt格式如下
```
# 任务
   创建一张组织架构表，表结构如下：部门名称，部门编号，父部门，是否有效。
# 要求
 - 表名用t_admin_rms_zzjg,
 - 字段要求：字符串类型使用'varchar(255)'，整数类型使用'int',浮点数类型使用'float'，日期和时间类型使用'datetime'，布尔类型使用'boolean'，文本类型使用'text'，大文本类型使用'longtext'，大整数类型使用'bigint'，大浮点数类型使用'double。
 - 表头需要加入主键字段，序号 XH varchar(255)
 - 表最后需加入固定字段：创建人-CJR varchar(50)，创建时间-CJSJ datetime，修改人-XGR varchar(50)，修改时间-XGSJ datetime。
 - 字段命名使用工具返回内容作为字段命名
 - 常用字段需要添加索引
 - 每个字段需要添加注释，表注释也需要
 - 创建完成后生成5条真实数据
```

#### 效果图
![image](https://github.com/user-attachments/assets/e95dc104-4e26-426a-acd4-d3b15ad654f5)

![image](https://github.com/user-attachments/assets/618f610e-5188-4c40-aeaa-cfbe7b0762c3)

![image](https://github.com/user-attachments/assets/4c91c8d1-4a42-41f4-8fe2-e46df0f08daa)

![image](https://github.com/user-attachments/assets/328a2cce-11ac-48f0-818a-1f1d231d7013)

![image](https://github.com/user-attachments/assets/db265aaf-a3e9-41b4-bf7a-235ba34ed4cd)

![image](https://github.com/user-attachments/assets/c67e2948-78af-4c8a-b1ff-6a7172bbb6f8)

![image](https://github.com/user-attachments/assets/9f6215e6-51fc-4e32-9d21-3e19abfa4bc6)

![image](https://github.com/user-attachments/assets/f10fc2b7-ac41-4f2c-a163-c7683bf2fabe)




