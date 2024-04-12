from flask import Flask, request, render_template, flash, redirect, url_for
from transformers import pipeline
import nltk
from textblob import TextBlob
from newspaper import Article
from datetime import datetime
from urllib.parse import urlparse
import validators
import requests

nltk.download('punkt')
app = Flask(__name__)

# Initialize the summarization pipeline
summarizer = pipeline("summarization", model="t5-base")

@app.route('/')
def home():
    return render_template('index.html')

def get_website_name(url):
    # Extract the website name from the URL
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    return domain

@app.route('/web', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        # Check if the input is a valid URL

        if not validators.url(url):
            flash('Please enter a valid URL.')
            return redirect(url_for('index'))
        
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
        except requests.RequestException:
            flash('Failed to download the content of the URL.')
            return redirect(url_for('index'))
        
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()  # Perform natural language processing

        title = article.title
        authors = ', '.join(article.authors)
        if not authors:
            authors = get_website_name(url)  # Set the author field to the website name
        publish_date = article.publish_date.strftime('%B %d, %Y') if article.publish_date else "N/A"

        # Manually adjust the summary length by selecting a certain number of sentences
        article_text = article.text
        sentences = article_text.split('.')
        max_summarized_sentences = 5  # Adjust the number of sentences as needed
        summary = '.'.join(sentences[:max_summarized_sentences])

        top_image = article.top_image  # Get the top image URL

        if summary == "":
            flash('Please enter a valid URL.')
            return redirect(url_for('index'))

        return render_template('web.html', title=title, authors=authors, publish_date=publish_date, summary=summary, top_image=top_image)

    return render_template('web.html')

@app.route('/summarize', methods=['POST'])
def summarize(): 
    # Get the input text from the form
    article = request.form['article']

    # Perform summarization using the pipeline
    summary = summarizer(article, max_length=130, min_length=30, do_sample=False)

    # Render the summary template with the generated summary
    return render_template('summary.html', summary=summary[0]['summary_text'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
