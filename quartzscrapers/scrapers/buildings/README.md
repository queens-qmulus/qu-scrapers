## Buildings

Resources on every building on Queen's campus.

##### Resource Link
http://queensu.ca/maps

##### Class Name
```python
quartzscrapers.Buildings
```

##### Parameters

```python
import quartzscrapers as qs

# Default
qs.Buildings.scrape()

# Custom location
qs.Buildings.scrape(location='./some/location')
```

##### Data Schema
```javascript
{
  _parameter: String,
  code: String,
  name: String,
  address: String,
  latitude: Number,
  longitude: Number,
  campus: String,
  polygon: [[Number, Number]]
}
```

##### Data Schema: Sample
```json
{
  "_parameter": "coastal",
  "code": "COASTAL",
  "name": "Coastal Engineering Lab",
  "address": "950 Johnson Street",
  "latitude": 44.2303584,
  "longitude": -76.5170842,
  "campus": "west",
  "polygon": [
    [
      3,
      5
    ],
    [
      6,
      3
    ],
    [
      6,
      5
    ],
    [
      3,
      7
    ],
    [
      3,
      5
    ]
  ]
}
```

##### JSON File Format
`<_parameter>.json`

##### JSON File Format: Sample
`coastal.json`

##### Developer Notes
