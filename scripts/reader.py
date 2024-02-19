"""Reader

This scritp aims to retrieve relevent articles, check it hasn't published them yet
and summarizes and stores them in a dataframe. This dataframe will be used by the
writer to publish tweets.

Structure:
    1. Retrieve Articles
        1.1 Imports, Variables, Functions
        1.2 Fetching Recent Papers
        1.3 Fetching Citation CountS
        1.4 Filter Papers
        1.5 Store in DataFrame
    2. Summarize Articles
        2.1 Imports, Variables, Functions
        2.2 Load Model
        2.3 Summarize Articles
        2.4 Save DataFrame
"""
# 1. Retrieve Articles
# 1.1 Imports, Variables, Functions
# imports
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import logging, pandas as pd, json, os, sys

logging.basicConfig(level=logging.INFO)

from tqdm.contrib.concurrent import (
    process_map,
)  # Import process_map for multiprocessing

# variables
min_citations = 1 

journals = [
    "Bioinformatics",
    "BMC Bioinformatics",
    "PLOS Computational Biology",
    "Journal of Computational Biology",
    "Journal of Biomedical Informatics",
    "Journal of Cheminformatics",
    "Molecular Informatics",
    "Journal of Chemical Information and Modeling",
    "IEEE/ACM Transactions on Computational Biology and Bioinformatics",
    "Computational and Structural Biotechnology Journal",
    "Briefings in Bioinformatics",
    "Systems Biology and Applications",
    "BioSystems",
    "Algorithms for Molecular Biology",
    "BioData Mining",
    "Proteins: Structure, Function, and Bioinformatics",
    "Molecular Systems Biology",
    "Cell Systems",
    "GigaScience",
    "Artificial Intelligence in Medicine",
    "Journal of Artificial Intelligence Research",
    "Frontiers in Bioengineering and Biotechnology",  # AI applications
    "Pattern Recognition in Bioinformatics",
    "Synthetic and Systems Biotechnology",  # AI applications
    "Neural Networks",  # Applications in bioinformatics
    "Machine Learning in Bioinformatics",
    "International Journal of Data Mining and Bioinformatics",
    "Genomics, Proteomics & Bioinformatics",
    "Bioinformatics and Biology Insights",
    "Applied Soft Computing",  # Relevant for AI applications in bioinformatics
    "Evolutionary Bioinformatics",
    "Journal of Machine Learning Research",  # Applications in bioinformatics
    "Knowledge-Based Systems",  # Relevant for AI applications in bioinformatics
    "BMC Systems Biology",  # AI applications in systems biology
    "Nature Machine Intelligence",  # AI with applications in bioinformatics and biotechnology
    "Nature",
    "Nature Biomedical Engineering",  # While broader, it includes significant bioinformatics research.
]
    # "Nature Biomedical Engineering",  # While broader, it includes significant bioinformatics research.
    # "Patterns (Cell Press)",  # Focuses on data science that impacts science and society, including bioinformatics.
# "Nucleic Acids Research",
# "BMC Genomics",
# "BMC Systems Biology",
# "BMC Evolutionary Biology",
# "PLOS Genetics",
# "Genome Research",
# "Genome Biology",
# "Journal of Proteome Research",

journal_queries = ['"' + journal + '"[Journal]' for journal in journals]

# query = 'chemoinformatics OR "AI biomedicine"'
query = " OR ".join(journal_queries)


# functions
def fetch_citation_count(pmid):
    """
    Fetch citation count for a given PMID.
    """
    elink_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
    params = {
        "dbfrom": "pubmed",
        "db": "pubmed",
        "id": pmid,
        "linkname": "pubmed_pubmed_citedin",  # Link to citing articles
        "retmode": "xml",
    }

    response = requests.get(elink_url, params=params)
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        citation_count = len(root.findall(".//LinkSetDb/Link"))
        return citation_count
    return 0  # Return 0 if unable to fetch citation count


def fetch_citations_for_papers(papers):
    """
    Fetch citation counts for a list of papers in parallel.
    """
    pmids = [paper["pmid"] for paper in papers]
    citation_counts = process_map(fetch_citation_count, pmids, max_workers=10)
    for paper, citation_count in zip(papers, citation_counts):
        paper["citations"] = citation_count
    return papers


def fetch_recent_papers(query, days_ago=90, n_articles=10000):
    """
    Fetch recent papers from PubMed based on a query and include citation counts.
    """
    # Calculate date range
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days_ago)
    start_date_str = start_date.strftime("%Y/%m/%d")
    end_date_str = end_date.strftime("%Y/%m/%d")

    # PubMed API endpoint
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": f'({query}) AND ("{start_date_str}"[Date - Publication] : "{end_date_str}"[Date - Publication])',
        "retmax": n_articles,
        "usehistory": "y",
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        webenv = root.find(".//WebEnv").text
        query_key = root.find(".//QueryKey").text

        # Fetch actual paper details using efetch
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "query_key": query_key,
            "WebEnv": webenv,
            "retmode": "xml",
            "rettype": "abstract",
            "retmax": n_articles,
        }
        fetch_response = requests.get(fetch_url, params=fetch_params)
        if fetch_response.status_code == 200:
            fetch_root = ET.fromstring(fetch_response.content)
            papers = []
            for article in fetch_root.findall(".//PubmedArticle"):
                title = article.find(".//ArticleTitle").text
                pmid = article.find(".//PMID").text
                link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

                # Extract keywords
                keyword_list = article.find(".//KeywordList")

                keywords = (
                    [keyword.text for keyword in keyword_list.findall(".//Keyword")]
                    if keyword_list is not None
                    else []
                )

                # Attempt to extract the DOI
                article_doi = article.find(".//ArticleId[@IdType='doi']")
                doi = article_doi.text if article_doi is not None else None

                # Construct the link to the full article using DOI
                doi_link = (
                    f"https://doi.org/{doi}" if doi else "Link not available"
                )

                # New code to fetch abstracts
                abstract_text = article.find(".//Abstract/AbstractText")
                abstract = (
                    abstract_text.text
                    if abstract_text is not None
                    else "Abstract not available"
                )

                papers.append(
                    {
                        "title": title,
                        "pmid": pmid,
                        "link": link,
                        "doi_link": doi_link,
                        "keywords": keywords,
                        "abstract": abstract,
                    }
                )
            return papers
    return "Failed to fetch papers or no papers found."


def load_tweeted_pmids():
    try:
        with open(os.path.join("..","results","tweeted.json"), 'r') as f:
            return set(json.load(f))  # Load and convert list back to set
    except FileNotFoundError:
        return set()  # Return an empty set if the file doesn't exist

tweeted_pmids = load_tweeted_pmids()

# 1.2 Fetching Recent Papers
papers = fetch_recent_papers(query)
logging.info(f"Nº of papers: {len(papers)}")

# 1.3 Fetching Citation Counts
papers = fetch_citations_for_papers(papers)
logging.info(
    f"Nº of papers w/ citations in less than 3 months: {len([p for p in papers if p['citations'] > 0])}"
)

# 1.4 Filter Papers

# filter papers with less than min_citations
papers = [p for p in papers if p["citations"] >= min_citations]

# filter papers which have already been tweeted by writer
tweeted_pmids = load_tweeted_pmids()
papers = [p for p in papers if p["pmid"] not in tweeted_pmids]

# 1.5 Store in DataFrame
df_papers = pd.DataFrame(papers)


# 2 Summarize Articles
# 2.1 Imports, Variables, Functions
# imports
from transformers import pipeline
import os, sys
from tqdm import tqdm

# variables
prompt = "Summarize the following abstract from a scientific article: %s"
model_path = os.path.join("..", "data", "llama-2-7b-chat.Q4_K_M.gguf")
output_path = os.path.join("..", "results", "papers_to_tweet.csv")

# functions


# 2.2 Load the Model
summarizer = pipeline("summarization", model="../bart-large-cnn")

# 2.3 Summarize Articles
abstract_summaries = list()
for index, row in tqdm(df_papers.iterrows()):
    if row["abstract"] is not None:
        abstract_summary = summarizer(
            prompt % row["abstract"], max_length=30, min_length=15, do_sample=False
        )[0]["summary_text"]
        # Sometimes we will have it cutting the summary in the middle of a sentence
        # which we don't want
        sentences = abstract_summary.split(".")
        all_except_last = sentences[:-1]
        join_except_last = ".".join(all_except_last)
        if len(join_except_last) > 0 & (abstract_summary != "Abstract not available"):
            abstract_summary = join_except_last + "."
        else:
            # If the summary has not one complete sentence, we will 
            # drop it completely ! ! !
            abstract_summary = None 
    else:
        abstract_summary = None
    abstract_summaries.append(abstract_summary)

df_papers["abstract_summary"] = abstract_summaries




# 2.4 Save DataFrame
df_papers.to_csv(output_path, index=False)
logging.info(f"DataFrame saved in {output_path}")