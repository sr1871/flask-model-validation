from typing import Any

import pytest
from flask import Flask
from sqlalchemy import event

from flask_model_validation import SQLAlchemyModelValidation
from flask_model_validation.models import mixins
from flask_model_validation.expressions import and_, or_, _


@pytest.fixture
def User(db: SQLAlchemyModelValidation, UserTeam) -> Any:
    """Creates the User model."""

    class User(db.Model, mixins.IdMixin, mixins.TimestampMixin):
        name = db.ValidateColumn(db.String(24), nullable=False)
        age = db.ValidateColumn(db.Integer)
        email = db.ValidateColumn(db.String(24))
        company_id = db.ValidateColumn(db.Integer, db.ForeignKey("company.id"))

        company = db.relationship("Company", back_populates="users")
        teams = db.relationship("UserTeam", back_populates="user")
        teams_has = db.relationship(
            "Team",
            secondary=lambda: UserTeam.__table__,
            secondaryjoin="Team.id==UserTeam.team_id",
            viewonly=True,
        )

    return User


@pytest.fixture
def Company(db: SQLAlchemyModelValidation) -> Any:
    """Creates the Company model."""

    class Company(db.Model, mixins.IdMixin, mixins.TimestampMixin):
        name = db.ValidateColumn(db.String(24), nullable=False)

        users = db.relationship("User", back_populates="company")
        teams = db.relationship("Team", back_populates="company")

    return Company


@pytest.fixture
def Team(db: SQLAlchemyModelValidation) -> Any:
    """Creates the Team model."""

    class Team(db.Model, mixins.IdMixin, mixins.TimestampMixin):
        name = db.ValidateColumn(db.String(24), nullable=False)
        company_id = db.ValidateColumn(
            db.Integer, db.ForeignKey("company.id"), nullable=False
        )

        company = db.relationship("Company", back_populates="teams")
        users = db.relationship("UserTeam", back_populates="team", lazy="dynamic")

    return Team


@pytest.fixture
def UserTeam(db: SQLAlchemyModelValidation) -> Any:
    """Creates the UserTeam model."""

    class UserTeam(
        db.Model,
        mixins.IdMixin,
    ):
        user_id = db.ValidateColumn(db.Integer, db.ForeignKey("user.id"))
        team_id = db.ValidateColumn(db.Integer, db.ForeignKey("team.id"))

        user = db.relationship("User", back_populates="teams", foreign_keys=[user_id])
        team = db.relationship("Team", back_populates="users", foreign_keys=[team_id])

    return UserTeam


@pytest.fixture(autouse=True)
def create_all(
    app: Flask, db: SQLAlchemyModelValidation, User, Company, Team, UserTeam
):
    """Using the app context, create the models and populate the db."""
    with app.app_context():
        # Sets the database case sensitive.
        event.listen(
            db.engine,
            "connect",
            lambda db, _: db.execute("pragma case_sensitive_like=ON"),
        )
        db.create_all()
        companies = [
            {"name": "Company One"},
            {"name": "Company Two"},
            {"name": "Company Three"},
        ]
        users = [
            {"name": "User One", "age": 18, "email": "user1@test.com"},
            {"name": "User Two", "age": 25, "email": "user2@mail.com"},
            {"name": "User OneTree", "age": 29, "email": "user3@test.com"},
        ]
        teams = [
            {"name": "Team One"},
            {"name": "Team Two"},
            {"name": "Team Three"},
        ]

        for idx in range(3):
            company = Company(**companies[idx])
            company.save(flush=True)
            team = Team(**teams[idx], company=company)
            team.save(flush=True)
            user = User(company_id=company.id, **users[idx])
            user.save(commit=True)

        for team in Team.query.all():
            user = User.query.first()
            ut = UserTeam(user=user, team=team)
            ut.save(commit=True)

        user = User(name="Other")
        user.save(commit=True)

        company = Company(name="Without employees")
        company.save(commit=True)


@pytest.mark.usefixtures("app_ctx")
def test_string_query(User):
    """GIVEN The user want to do a query with strings
    WHEN the models have been created
    THEN the query should be return right data.
    """
    assert User.query.find(name="User One").count() == 1
    assert User.query.find(name__ne="User One").count() == 3
    assert User.query.find(name__startswith="user").count() == 0
    assert User.query.find(name__istartswith="user").count() == 3
    assert User.query.find(name__not_istartswith="user").count() == 1
    assert User.query.find(name__endswith="one").count() == 0
    assert User.query.find(name__iendswith="one").count() == 1
    assert User.query.find(name__not_iendswith="one").count() == 3
    assert User.query.find(name__contains="one").count() == 0
    assert User.query.find(name__icontains="one").count() == 2
    assert User.query.find(company__name="Company One").count() == 1
    assert User.query.find(company__name__ne="Company One").count() == 2
    assert User.query.find(teams__is_empty=True).count() == 3
    assert User.query.find(teams__is_empty=False).count() == 1
    assert User.query.find(teams__has=[1]).count() == 1
    assert User.query.find(teams__not_has=[1]).count() == 3


@pytest.mark.usefixtures("app_ctx")
def test_int_query(User):
    """GIVEN The user want to do a query with integers
    WHEN the models have been created
    THEN the query should be return right data.
    """
    assert User.query.find(age=18).count() == 1
    assert User.query.find(age=None).count() == 1
    assert User.query.find(age__ne=18).count() == 2
    assert User.query.find(age__gt=18).count() == 2
    assert User.query.find(age__ge=18).count() == 3
    assert User.query.find(age__not_ge=29).count() == 2
    assert User.query.find(age__lt=29).count() == 2
    assert User.query.find(age__le=29).count() == 3
    assert User.query.find(age__in=[18, 25]).count() == 2
    assert User.query.find(age__not_in=[18, 25]).count() == 1


@pytest.mark.usefixtures("app_ctx")
def test_expressions_query(User):
    """GIVEN The user want to do a query with expressions
    WHEN the models have been created
    THEN the query should be return right data.
    """
    assert User.query.find(or_(name="User One", age=29)).count() == 2
    assert User.query.find(or_(_(name="User One"), _(name="User Two"))).count() == 2
    assert User.query.find(and_(name="User One", age=29)).count() == 0
    assert User.query.find(and_(name="User One", age=18)).count() == 1
    assert (
        User.query.find(
            or_(and_(name="User One", age=18), and_(name="User Two", age=25))
        ).count()
        == 2
    )


@pytest.mark.usefixtures("app_ctx")
def test_join_query(User):
    """GIVEN The user want to do a query with joins
    WHEN the models have been created
    THEN the query should be return right data.
    """
    assert (
        User.query.cjoin(teamuser="teams", team="teamuser__team")
        .find(team__id=1)
        .count()
        == 1
    )
    # Inner Join
    assert User.query.cjoin(company="company").find().count() == 3
    # Left Join
    assert User.query.cjoin(company="-company").find().count() == 4
