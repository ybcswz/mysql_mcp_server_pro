import nltk
nltk.download('omw-1.4')

from nltk.corpus import wordnet as wn

# 获取中文词的同义词和词义
def get_synonyms(word):
    synsets = wn.synsets(word, lang='cmn')  # 使用中文代码'cmn'
    synonyms = set()
    for syn in synsets:
        for lemma in syn.lemmas('cmn'):
            synonyms.add(lemma.name())
    return synonyms



from sentence_transformers import SentenceTransformer, util

# 加载预训练的 Sentence-BERT 模型
model = SentenceTransformer('all-MiniLM-L6-v2')

# 计算语义相似度
def is_semantically_similar(keyword, text, threshold=0.7):
    # 将 keyword 和 text 转换为向量
    embeddings = model.encode([keyword.lower(), text.lower()])
    # 计算余弦相似度
    similarity = util.cos_sim(embeddings[0], embeddings[1])
    return similarity.item() >= threshold

# word = "收益"
# synonyms = get_synonyms(word)
# print(f"{word}的同义词：{synonyms}")
#
# print(is_semantically_similar('收益', '收入'))