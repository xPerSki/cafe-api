from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from random import choice

app = Flask(__name__)


# CREATE DB
class Base(DeclarativeBase):
    pass


# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Cafe TABLE Configuration
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        dictionary = {}
        for col in self.__table__.columns:
            dictionary[col.name] = getattr(self, col.name)
        return dictionary


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/random", methods=["GET"])
def random():
    query = db.select(Cafe).order_by(Cafe.id)
    result = db.session.execute(query)
    all_cafes = result.scalars().all()
    random_cafe = choice(all_cafes)
    return jsonify(cafe=random_cafe.to_dict())


@app.route("/all", methods=["GET"])
def get_all():
    query = db.select(Cafe).order_by(Cafe.id)
    result = db.session.execute(query)
    cafes = result.scalars().all()
    return jsonify(cafes=[cafe.to_dict() for cafe in cafes])


@app.route("/search", methods=["GET"])
def search():
    loc = request.args.get("loc")
    query = db.select(Cafe).where(Cafe.location == loc.title())
    result = db.session.execute(query)
    found_cafes = result.scalars().all()

    if found_cafes:
        return jsonify(cafes=[cafe.to_dict() for cafe in found_cafes])
    else:
        return jsonify(errors={"Not Found": "Sorry, we don't have a cafe at this location."}), 404


@app.route("/add", methods=["POST"])
def add():
    new_cafe = Cafe(
        name=request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("loc"),
        has_sockets=bool(request.form.get("sockets")),
        has_toilet=bool(request.form.get("toilet")),
        has_wifi=bool(request.form.get("wifi")),
        can_take_calls=bool(request.form.get("calls")),
        seats=request.form.get("seats"),
        coffee_price=request.form.get("coffee_price"),
    )
    db.session.add(new_cafe)
    db.session.commit()

    return jsonify(response={"success": "Successfully added the new cafe."}), 200


@app.route("/update-price/<int:cafe_id>", methods=["PATCH"])
def update_price(cafe_id):
    if request.method == "PATCH":
        query = db.select(Cafe).where(Cafe.id == cafe_id)
        result = db.session.execute(query)
        found_cafe = result.scalar()

        if found_cafe:
            new_price = request.args.get("new_price")
            found_cafe.coffee_price = new_price
            db.session.commit()
            return jsonify(success="Successfully updated the price."), 200
        else:
            return jsonify(errors={"Not Found": "Sorry, a cafe with that id was not found in the database."}), 404


@app.route("/report-closed/<int:cafe_id>", methods=["DELETE"])
def close(cafe_id):
    query = db.select(Cafe).where(Cafe.id == cafe_id)
    result = db.session.execute(query)
    found_cafe = result.scalar()
    api_key = request.args.get("api_key")

    if api_key == "SecretAPIKey":
        if found_cafe:
            db.session.delete(found_cafe)
            db.session.commit()
            return jsonify(success="Successfully deleted cafe."), 200
        else:
            return jsonify(errors={"Not Found": "Cafe id not found."}), 404
    else:
        return jsonify(errors={"Not Authorized": "You are not authorized to do this action"}), 402


if __name__ == '__main__':
    app.run(debug=True)
