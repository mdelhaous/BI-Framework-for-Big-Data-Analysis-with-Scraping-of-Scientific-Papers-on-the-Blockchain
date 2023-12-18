from pymongo import MongoClient
import pandas as pd
from fastapi import FastAPI
from typing import Union
import json
from fastapi.middleware.cors import CORSMiddleware

client = MongoClient('localhost',27017)  # 27017 is the default port number for mongodb
db=client["local"]
scFinal=db["myData"]
df = pd.DataFrame(list(scFinal.find()))
del df['_id']
app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/test_mouad")
def tt():
    # result = scFinal.update_many({"Publication Year": 2024}, {"$set": {"Publication Year": 0}})
    documents_2023 = scFinal.find({"Publication Year": 2023}).sort("_id", -1).limit(500)
    document_ids = [doc["_id"] for doc in documents_2023]
    result = scFinal.delete_many({"_id": {"$in": document_ids}})
    # # Duplicate documents and set "Publication Year" to 2024
    # for document in documents_2023:
    #     document_copy = document.copy()
    #     new_document = {
    #         "Publication Year": 2023,
    #         "Document Title" : document_copy["Document Title"],
    #         "Authors" : document_copy["Authors"],
    #         "Universities" : document_copy["Universities"],
    #         "Citations" : document_copy["Citations"],
    #         "Affiliations" : document_copy["Affiliations"],
    #         "Publisher" : document_copy["Publisher"],
    #         "DOI" : document_copy["DOI"]
    #     }
    #     scFinal.insert_one(new_document)

@app.get("/nb_article")
def getNbArticles():
    return {"nb_articles": df.shape[0],
        "nb_articles_acm": df[df.Publisher=="Science direct"].shape[0],
        "nb_articles_science": df[df.Publisher=="ACM"].shape[0],
        "nb_articles_ieee": df[df.Publisher=="IEEE"].shape[0]}


@app.get("/nb_article")
def getNbArticlesByYearAndPulisher():
    acm=df[df.Publisher=="ACM"].groupby('Publication Year').count()
    ieee=df[df.Publisher=="IEEE"].groupby('Publication Year').count()
    science=df[df.Publisher=="Science direct"].groupby('Publication Year').count()

@app.get("/all_articles")
def getArticles():
    data=[]
    result=scFinal.find({})
    for i in result:
        data.append({
            "Titre":i['Document Title'],
            "year":i['Publication Year'],
            #"Authors":i['Authors'],
            "Citations":i['Citations'],
            "Afficliation":i['Affiliations'],
            "Publisher":i['Publisher'],
            "doi":i['DOI']
        })
    return data

@app.get("/countries")
def getCountCountries():
    data=[]
    grouped = df.groupby("Affiliations").count()
    # Iterate through the groups and counts
    for group, count in grouped["Citations"].items():
        data.append({
            'country':group,
            'count': count
        })
    return data
    
@app.get("/years")
def getCountYears():
    data=[]
    grouped = df.groupby("Publication Year").count()
    # Iterate through the groups and counts
    for group, count in grouped["Citations"].items():
        data.append({
            'Year':group,
            'count': count
        })
    return data

    
@app.get("/citations")
def getCountCitations():
    data=[]
    grouped = df.groupby("Affiliations")["Citations"].sum()
    # Iterate through the groups and counts
    for group, count in grouped.items():
        data.append({
            'Country':group,
            'Citations': count
        })
    return data

@app.get("/citationsByYear")
def citationsByYear():
    data=[]
    grouped = df.groupby("Publication Year")["Citations"].sum()
    # Iterate through the groups and counts
    for group, count in grouped.items():
        data.append({
            'Year':group,
            'Citations': count
        })
    return data


    
@app.get("/citationsCountries")
def getCountCitationsAndCountries():
    data=[]
    grouped1 = df.groupby("Affiliations").count()
    grouped = df.groupby("Affiliations")["Citations"].sum()
    # Iterate through the groups and counts
    for group1, group2 in zip(grouped.items(), grouped1["Publication Year"].items()):
        data.append({
            'Country':group1[0],
            'Citations': group1[1],
            'count':group2[1]
        })
    return data

@app.get("/citationsByPublisher")
def getCountCitationsByPublisherr():
    data=[]
    grouped = df.groupby("Publisher")["Citations"].sum()
    # Iterate through the groups and counts
    for group, count in grouped.items():
        data.append({
            'Publisher':group,
            'Citations': count
        })
    return data