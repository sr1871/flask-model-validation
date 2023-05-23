# Flask-model-validation

Flask-model-validation is an extension for [Flask-SQLAlchemy](https://github.com/pallets-eco/flask-sqlalchemy) that adds support for validating the model before commit it to the database. It adds new functions to query and save the model easily.

## Installation

Install using [pip](https://pip.pypa.io)

```bash
pip install Flask-model-validation
```

## Setup the extension
It should be initialized like `Flask-SQLAlchemy` extension.

For more information see the [Flask-SQLAlchemy documentation](https://flask-sqlalchemy.palletsprojects.com/en/3.0.x/)

```python
from flask import Flask
from flask_model_validation import SQLAlchemyModelValidation

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
db = SQLAlchemyModelValidation()
db.init_app(app)
```

## Features
Flask-model-validation includes several new features.

- [Validation](docs/validation.md)
- [Mixins](docs/mixins.md)
- [Saving the model](docs/save.md)
- [Deleting the model](docs/delete.md)
- [Extra model features](docs/model_features.md)
- [query to the database](docs/query.md)


## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
