## Courses

Resources on every course offered at Queen's University.

These resources are split into different schemas, the main reason being that
`courses` and `departments` are constant factual information, whereas course
`sections` are constantly changing.

There’s also the consideration of *relative* course information, such as
ANAT 416 in Fall 2018 vs ANAT 416 in Winter 2017, which will have different
enrollment capacities, waitlists, lecture slots & times, etc.

The three schemas are:

- [Courses](#courses)
- [Departments](#departments)
- [Sections](#sections)

##### Resource Link
https://saself.ps.queensu.ca

##### Class Name
```python
quartzscrapers.Courses
```

##### Parameters

```python
import quartzscrapers as qs

# Default
qs.Courses.scrape()

# Custom location
qs.Courses.scrape(location='./some/location')
```

### Courses
Resources purely about a course, such as its description, course code, and requirements.

##### Data Schema
```javascript
{
  id: String,
  department: String,
  course_code: String,
  course_name: String,
  campus: String,
  description: String,
  grading_basis: String,
  course_components: { type: Map, of: String }, // handles arbitrary keys
  requirements: String,
  add_consent: String,
  drop_consent: String,
  academic_level: String,
  academic_group: String,
  academic_org: String,
  units: String,
  CEAB: {
    math: Number,
    basic_sci: Number,
    comp_st: Number,
    eng_sci: Number,
    end_des: Number
  }
}
```

##### Data Schema: Sample
```json
{
  "id": "APSC-291",
  "department": "APSC",
  "course_code": "291",
  "course_name": "Engineering Communications I",
  "campus": "Main",
  "description": "This course provides an introduction to effective engineering...",
  "grading_basis": "Graded",
  "course_components": {
    "laboratory": "Required",
    "lecture": "Required"
  },
  "requirements": "APSC291 excludes CHEE260, ELEC291, GEOL291, GEOL292 and MECH290...",
  "add_consent": "Instructor Consent Required",
  "drop_consent": "Instructor Consent Required",
  "academic_level": "Undergraduate",
  "academic_group": "Fac of Engineering & Appl Sci",
  "academic_org": "Engineer (not dept specific)",
  "units": 1.0,
  "CEAB": {
    "math": 0,
    "basic_sci": 0,
    "comp_st": 12.0,
    "eng_sci": 0,
    "end_des": 0
  }
}
```

##### JSON File Format
`<department_course_code>.json`

##### JSON File Format: Sample
`APSC_291.json`

##### Developer Notes
--

### Departments
Resources about departments. Only contains `code` and `name`.

##### Data Schema
```javascript
{
  code: String,
  name: String
}
```

##### Data Schema: Sample
```json
{
  "code": "CISC",
  "name": "ComputingInformation Science"
}
```

##### JSON File Format
`<code>.json`

##### JSON File Format: Sample
`CISC.json`

##### Developer Notes
--

### Sections
Resources about course departments, such as lecture times, instructors, etc.

##### Data Schema
```javascript
{
  id: String,
  year: String,
  term: String,
  department: String,
  course_code: String,
  course_name: String,
  units: Number,
  campus: String,
  academic_level: String,
  course_sections: [{
    section_name: String,
    section_type: String,
    section_number: String,
    class_number: Number,
    dates: [{
      day: String,
      start_time: String,
      end_time: String,
      start_date: String,
      end_date: String,
      location: String,
      instructors: [String],
    }],
    combined_with: [Number],
    enrollment_capacity: Number,
    enrollment_total: Number,
    waitlist_capacity: Number,
    waitlist_total: Number,
    last_updated: String
  }]
}
```

##### Data Schema: Sample
```json
{
  "id": "2018-FA-U-M-CISC-235",
  "year": "2018",
  "term": "Fall",
  "department": "CISC",
  "course_code": "235",
  "course_name": "Data Structures",
  "units": 3.0,
  "campus": "Main",
  "academic_level": "Undergraduate",
  "course_sections": [
    {
      "section_name": "001-LEC",
      "section_type": "Lecture",
      "section_number": "001",
      "class_number": "4609",
      "dates": [
        {
          "day": "Monday",
          "start_time": "11:30",
          "end_time": "12:30",
          "start_date": "2018-09-06",
          "end_date": "2018-11-30",
          "location": "JEFFERY RM126",
          "instructors": [
            "Dawes, Robin"
          ]
        },
        {
          "day": "Tuesday",
          "start_time": "13:30",
          "end_time": "14:30",
          "start_date": "2018-09-06",
          "end_date": "2018-11-30",
          "location": "JEFFERY RM126",
          "instructors": [
            "Dawes, Robin"
          ]
        },
        {
          "day": "Thursday",
          "start_time": "12:30",
          "end_time": "13:30",
          "start_date": "2018-09-06",
          "end_date": "2018-11-30",
          "location": "JEFFERY RM126",
          "instructors": [
            "Dawes, Robin"
          ]
        }
      ],
      "combined_with": [],
      "enrollment_capacity": 100,
      "enrollment_total": 28,
      "waitlist_capacity": 10,
      "waitlist_total": 0,
      "last_updated": "2018-07-25T03:26:41.173072-04:00"
    }
  ]
}
```

##### JSON File Format
`<year>_<term>_<academic_level>_<campus>_<department>_<course_code>.json`

##### JSON File Format: Sample
`2018_Fall_Undergraduate_Main_CISC_235.json`

#### Developer Notes

##### Section Uniqueness
Multiple courses with the same ID can exist. Such as MATH121 for main
campus, bader campus, or online. In order for a course listing to be
unique, these 6 datapoints must be distinct as a bundle:

- `year`
- `term`
- `academic_level`
- `campus`
- `department`
- `course_code`

E.g: A formatted ID would be `2018_Fall_Undergraduate_Main_CISC_235` if it
were a file, and `2018-Fall-Undergraduate-Main-CISC-235` otherwise.

##### Known key-values
The following keys have been found during scrapes. Some are exhaustive while others are variable:

##### `year`
Any

##### `term`
- `Fall`
- `Summer`
- `Winter`

##### `academic_level`
- `Undergraduate`
- `Graduate`
- `Undergraduate_Online`
- `Non_Credit`

##### `campus`
- `Main`
- `Bader`
- `None`

##### `department`
Any

##### `course_code`
Any

Note: For course header bundles, realize that `academic_level` and `campus` must be unique *as a pair*. For example, **MATH 121** has 3 valid pair possibilities:

1) `academic_level`: Undergraduate,  `campus`: Main
2) `academic_level`: Undergraduate,  `campus`: Bader
3) `academic_level`: Undergraduate_Online,  `campus`: Main