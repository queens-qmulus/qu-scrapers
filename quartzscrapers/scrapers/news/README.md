## News

Resources on various news outlets relating to Queen's University.

Because this is multiple scrapers masked as one, we'll organize this as sub-scrapers under a main one. The News scraper goes through a list of scrapers to start. All data schemas here are identical.

Current list of sub-scrapers:

- [Queen’s Journal](#queens-journal)
- [Queen’s Gazette](#queens-gazette)
- [Queen’s Alumni Review](#queens-alumni-review)
- [Smith Magazine](#smith-magazine)
- [Juris Diction](#juris-diction)

##### Class Name
```python
quartzscrapers.News
```

##### Parameters

```python
import quartzscrapers as qs

# Default. Scrape 'latest' news only
qs.News.scrape()

# Custom location
qs.News.scrape(location='./some/location')

# Scrape news since the beginning
qs.News.scrape(deep=True)

# Also applies to specific news outlets
qs.Journal.scrape()
qs.Gazette.scrape()
qs.SmithMagazine.scrape()
...
```

##### Data Schema
```javascript
{
  title: String,
  slug: String,
  url: String,
  published: Date,
  updated: Date,
  authors: [String],
  content: String,
  content_raw: String
}
```

##### Data Schema: Sample
```json
{
  "title": "AMS gathers for first assembly of the year",
  "slug": "queensjournal",
  "url": "http://www.queensjournal.ca/story/2019-09-20/news/ams-gathers-for-first-assembly-of-the-year",
  "published": "2019-09-20T00:00:00+00:00",
  "updated": "2019-09-20T00:00:00+00:00",
  "authors": [
    "Sydney Ko",
    "Carolyn Svonkin"
  ],
  "content": "The AMS kicked off its first assembly of the year by approving service and ...",
  "content_raw": "<div class=\"field field-name-body field-type-text-with-summary field-l..."
}
```

##### JSON File Format
`<YYYY-MM-DD>_<article_url_title>.json`

##### JSON File Format: Sample
`2019-09-20_ams-gathers-for-first-assembly-of-the-year.json`

### Queen's Journal
Subscraper under News scraper for Queen’s Journal. See [News](#news) for and data schema and usage.

##### Resource Link
http://www.queensjournal.ca

##### Class Name
```python
quartzscrapers.Journal
```
##### Developer Notes
Use boolean parameter `deep` to signify wanting a deep or shallow scrape.

`deep=False`: Scrape latest archive year. As of 2019, that would be... 2019.

`deep=True`: Scrape every article from every avaialble archive year. Queen's Journal goes as far back as September 2000.

### Queen's Gazette
Subscraper under News scraper for Queen’s Gazette. See [News](#news) for and data schema and usage.

##### Resource Link
http://queensu.ca/gazette/stories/all

##### Class Name
```python
quartzscrapers.Gazette
```

##### Developer Notes
Use boolean parameter `deep` to signify wanting a deep or shallow scrape.

`deep=False`: Scrape latest archive year. As of 2019, that would be... 2019.

`deep=True`: Scrape every article from every avaialble archive year. Queen's Journal goes as far back as December 2012.

### Queen's Alumni Review
Subscraper under News scraper for Queen’s Alumni Review. See [News](#news) for and data schema and usage.

Note: Alumni Review's website is a subsection of Gazette's website, and so it inherits from [Gazette](#queens-gazette)'s scraper.

##### Resource Link
http://queensu.ca/gazette/alumnireview/stories

##### Class Name
```python
quartzscrapers.AlumniReview
```

##### Developer Notes
--

### Smith Magazine
Subscraper under News scraper for Smith Magazine. See [News](#news) for and data schema and usage.

##### Resource Link
https://smith.queensu.ca/magazine/archive

##### Class Name
```python
quartzscrapers.SmithMagazine
```
##### Developer Notes
Smith Magazine has quarterly issues, unlike daily/weekly article releases as seen in other news sites. This means the ISO 8601 date format might not be correct, but is left in-tact for data consistency.

E.g.: *Winter 2017*, *Spring 2018*, etc are issue dates, which are converted to 2017-01-01 (year, first month, first day).

Use boolean parameter `deep` to signify wanting a deep or shallow scrape.

`deep=False`: Scrape latest issue. As of 2019, that would be Summer 2019.

`deep=True`: Scrape every available issue. Smith Magazine goes as far back as Summer 2008.

### Juris Diction
Subscraper under News scraper for Juris Diction: The magazine by and for Queen's Law students. See [News](#news) for and data schema and usage.

NOTE: As of 2019, this site is under construction and may need scraper updates.

##### Resource Link
http://www.juris-diction.ca

##### Class Name
```python
quartzscrapers.JurisDiction
```
##### Developer Notes
--