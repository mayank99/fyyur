# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ARRAY
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)
# db.create_all()
migrate = Migrate(app, db)
print(app.config['SQLALCHEMY_DATABASE_URI'])

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = "Venue"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    genres = db.Column(ARRAY(db.Text), nullable=True)

    shows = db.relationship("Show", backref=db.backref("venues"))

    def __repr__(self):
        return f"<Venue {self.id}: {self.name}>"


class Artist(db.Model):
    __tablename__ = "Artist"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    genres = db.Column(ARRAY(db.Text), nullable=True)

    shows = db.relationship("Show", backref=db.backref("artists"))

    def __repr__(self):
        return f"<Artist {self.id}: {self.name}>"


class Show(db.Model):
    __tablename__ = "Show"
    artist_id = db.Column(db.Integer, db.ForeignKey("Artist.id"), primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey("Venue.id"), primary_key=True)
    start_time = db.Column(db.DateTime)
    artist = db.relationship("Artist", backref=db.backref("venues"))
    venue = db.relationship("Venue", backref=db.backref("artists"))


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format):
    if format == "time":
        return value.strftime("%I:%M %p")
    elif format == "date":
        return value.strftime("%a %b %d")
    else:
        return value.strftime("%c")

app.jinja_env.filters["datetime"] = format_datetime

app.jinja_env.filters['count'] = len

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    all_venues = list(Venue.query.all())
    cities = set(map(lambda v: (v.city, v.state), all_venues))

    data = []
    for city in cities:
        data.append(
            {
                "city": city[0],
                "state": city[1],
                "venues": list(filter(lambda v: v.city == city[0] and v.state == city[1], all_venues)),
            }
        )
    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    search_term = request.form.get("search_term", "")
    data = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
    return render_template("pages/search_venues.html", results=data, search_term=search_term,)


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).first()
    upcoming_shows = list(filter(lambda s: s.start_time > datetime.now(), venue.shows))
    past_shows = list(filter(lambda s: s.start_time < datetime.now(), venue.shows))
    return render_template("pages/show_venue.html", venue=venue, upcoming_shows=upcoming_shows, past_shows=past_shows)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    try:
        new_venue = Venue(
            name=request.form["name"],
            city=request.form["city"],
            state=request.form["state"],
            address=request.form["address"],
            phone=request.form["phone"],
            genres=request.form.getlist("genres"),
            facebook_link=request.form["facebook_link"],
        )
        db.session.add(new_venue)
        db.session.commit()
        flash(f"Venue {new_venue.name} was successfully listed!")
    except:
        db.session.rollback()
        flash(f"An error occurred. Venue {request.form['name']} could not be listed.")
    finally:
        db.session.close()

    return redirect(url_for("show_venue", venue_id=new_venue.id))


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return jsonify({"success": True})


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    return render_template("pages/artists.html", artists=Artist.query.all())


@app.route("/artists/search", methods=["POST"])
def search_artists():
    search_term = request.form.get("search_term", "")
    data = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
    return render_template("pages/search_artists.html", results=data, search_term=search_term)


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id).first()
    upcoming_shows = list(filter(lambda s: s.start_time > datetime.now(), artist.shows))
    past_shows = list(filter(lambda s: s.start_time < datetime.now(), artist.shows))
    return render_template("pages/show_artist.html", artist=artist, upcoming_shows=upcoming_shows, past_shows=past_shows)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.filter_by(id=artist_id).first()
    form.state.data = artist.state
    form.genres.data = artist.genres
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    artist = Artist.query.get(artist_id)

    try:
        artist.name = request.form["name"]
        artist.city = request.form["city"]
        artist.state = request.form["state"]
        artist.phone = request.form["phone"]
        artist.genres = request.form.getlist("genres")
        artist.facebook_link = request.form["facebook_link"]
        artist.image_link = request.form["image_link"]
        artist.website = request.form["website"] or ""

        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter_by(id=venue_id).first()
    form.state.data = venue.state
    form.genres.data = venue.genres
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    venue = Venue.query.get(venue_id)

    try:
        venue.name = request.form["name"]
        venue.city = request.form["city"]
        venue.state = request.form["state"]
        venue.address = request.form["address"]
        venue.phone = request.form["phone"]
        venue.genres = request.form.getlist("genres")
        venue.facebook_link = request.form["facebook_link"]
        venue.image_link = request.form["image_link"]
        venue.website = request.form["website"] or ""

        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    try:
        new_artist = Artist(
            name=request.form["name"],
            city=request.form["city"],
            state=request.form["state"],
            phone=request.form["phone"],
            genres=request.form.getlist("genres"),
            facebook_link=request.form["facebook_link"],
            image_link=request.form["image_link"],
            website=request.form["website"],
        )
        db.session.add(new_artist)
        db.session.commit()
        flash(f"Artist {new_artist.name} was successfully listed!")
    except:
        db.session.rollback()
        flash(f"An error occurred. Artist {request.form['name']} could not be listed.")
    finally:
        db.session.close()

    return redirect(url_for("show_artist", artist_id=new_artist.id))


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    # upcoming_shows = list(filter(lambda s: s.start_time > datetime.now(), Show.query.all()))
    return render_template("pages/shows.html", shows=Show.query.all())


@app.route("/shows/create")
def create_shows():
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    try:
        show = Show(
            artist_id=request.form["artist_id"],
            venue_id=request.form["venue_id"],
            start_time=request.form["start_time"]
        )
        db.session.add(show)
        db.session.commit()
        flash("Show was successfully listed!")
    except:
        db.session.rollback()
        flash("An error occurred. Show could not be listed.")
    finally:
        db.session.close()

    return redirect(url_for("shows"))


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
