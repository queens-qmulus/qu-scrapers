## Textbooks

Resources on every textbook offered at Queen’s. Note that this resource refreshes its information annually.

##### Resource Link
https://www.campusbookstore.com/textbooks

##### Class Name
```python
quartzscrapers.Textbooks
```

##### Parameters

```python
import quartzscrapers as qs

# Default
qs.Textbooks.scrape()

# Custom location
qs.Textbooks.scrape(location='./some/location')
```

##### Data Schema
```javascript
{
  isbn_10: String,
  isbn_13: String,
  title: String,
  authors: [String],
  image: String,
  price_new: Number,
  price_used: Number,
  status: String,
  courses: [{
    year: String,
    term: String,
    department: String,
    course_code: String,
    url: String,
    instructor: [String]
  }]
}
```

##### Data Schema: Sample
```json
{
  "isbn_10": "1604561149",
  "isbn_13": "9781260186178",
  "title": "Paraxial Light Beams with Angular Momentum",
  "authors": [
    "A. Bekshaev",
    "Marat Samuilovich Soskin",
    "M. Vasnetsov"
  ],
  "image": "",
  "price_new": 129.95,
  "price_used": null,
  "status": "REQUIRED",
  "courses": [
    {
      "year": "2018",
      "term": "Spring",
      "department": "ANAT",
      "course_code": "100-700",
      "url": "https://www.campusbookstore.com/textbooks/search-engine/results?Course=ANAT19417",
      "instructor": "Leslie Mackenzie"
    },
    {
      "year": "2018",
      "term": "Summer",
      "department": "ANAT",
      "course_code": "100-700",
      "url": "https://www.campusbookstore.com/textbooks/search-engine/results?Course=ANAT19417",
      "instructor": "Leslie Mackenzie"
    },
    {
      "year": "2018",
      "term": "Winter",
      "department": "ANAT",
      "course_code": "100-700",
      "url": "https://www.campusbookstore.com/textbooks/search-engine/results?Course=ANATB03525",
      "instructor": "Les Mackenzie"
    }
  ]
}
```

##### JSON File Format
`<year>_<isbn_13>.json`

##### JSON File Format: Sample
`2018_9781260186178.json`

#### Developer Notes

##### Data Relationships
The same textbook can be required for multiple courses, making it a one-to-many relationship. This may require querying our resources for already-existing ISBNs, and editing the entry (appending to `courses`).

##### Missing Information
Queen’s websites unfortunately doesn't have gauranteed data integrity. This leaves the developer to fill in a lot of blanks for missing or incorrect information.

Missing/incorrect information here includes:

- Missing ISBN-10 (`isbn_10`)
- Missing authors (`authors`)
- Incorrect ISBN-13 (`isbn_13`)
- Incorrect book titles (`title`)

We fill in the void with an external tool; the [Google Books API](https://developers.google.com/books/) by scraping Queen’s textbook ISBNs and finding the missing/incorrect information **only**. Best practice is minimizing the use of external APIs as much as possible. Queen’s textbooks that have incorrect ISBNs will have no data recovery.

##### Data Inconsistencies
**Warning**: `courses` objects within textbook data could have some naming differences from other sources of truth, like SOLUS.

Example: ANAT 100 has its instructor listed as "Les Mackenzie". However, her actual name on SOLUS is "Leslie W. Mackenzie". See:

![screen shot 2019-10-03 at 9 46 57 pm](https://user-images.githubusercontent.com/9813064/41086266-744b76be-6a07-11e8-8c63-7810fdea7c2f.png)

Vs.

![screen shot 2019-10-03 at 9 46 57 pm](https://user-images.githubusercontent.com/9813064/41086272-7b51839a-6a07-11e8-9433-b9cbb35e544b.png)

Both "Les Mackenzie" and "Leslie Mackenzie" show up in various textbooks, referring to the same instructor.
