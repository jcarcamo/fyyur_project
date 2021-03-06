#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, \
                  url_for, request, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# connect to a postgresql database
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.Text())
    shows = db.relationship('Show', backref='venue', lazy=True, cascade='all, delete-orphan')
    def repr(self):
      return f'<Venue {self.id} {self.name}>'

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.Text())
    shows = db.relationship('Show', backref='artist', lazy=True, cascade='all, delete-orphan')
    def repr(self):
      return f'<Artist {self.id} {self.name}>'

class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key = True)
    start_time = db.Column(db.DateTime())  
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    def repr(self):
        return f'<Show {self.id} {self.description}, Start Time {self.start_time}>, \
          artist {self.artist_id}>, venue  {self.venue_id} '

# DONE Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  # From https://stackoverflow.com/questions/63269150/typeerror-parser-must-be-a-string-or-character-stream-not-datetime
  # instead of just date = dateutil.parser.parse(value)
  if isinstance(value, str):
      date = dateutil.parser.parse(value)
  else:
      date = value
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # Done: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = list()
  for state, city in (db.session.query(Venue.state, Venue.city).distinct(Venue.city) \
                .group_by(Venue.state, Venue.city).all()):
    location = dict()
    location["city"] = city
    location["state"] = state
    location["venues"] = db.session.query(Venue.id, Venue.name, \
                          db.func.count(Show.venue_id) \
                          .filter(Show.start_time > datetime.utcnow()) \
                          .label("num_upcoming_shows")) \
                          .filter(Venue.city == city) \
                          .outerjoin(Show, Venue.id == Show.venue_id) \
                          .group_by(Venue.id, Venue.name).all()
    data.append(location)                              
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # Done: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  
  # As seen in https://stackoverflow.com/questions/3325467/sqlalchemy-equivalent-to-sql-like-statement
  tag = request.form["search_term"]
  search = "%{}%".format(tag)
  venues = db.session.query(Venue.id, Venue.name, db.func.count(Show.venue_id) \
          .filter(Show.start_time > datetime.utcnow()) \
          .label("num_upcoming_shows")) \
          .filter(Venue.name.ilike(search)) \
          .outerjoin(Show, Venue.id == Show.venue_id) \
          .group_by(Venue.id, Venue.name).all()

  response={
    "count": len(venues),
    "data": venues
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # Done: replace with real venue data from the venues table, using venue_id

  # from datetime import datetime
  # from app import db, Venue, Show, Artist
  check_venue_exist(venue_id)
  past_shows =  db.session.query(Show.artist_id, Artist.name.label("artist_name"), \
                    Artist.image_link.label("artist_image_link"), \
                    Show.start_time) \
                    .join(Artist, Show.artist_id == Artist.id) \
                    .join(Venue, Show.venue_id == Venue.id) \
                    .filter(Show.start_time < datetime.utcnow()) \
                    .filter(Show.venue_id == venue_id) \
                    .all()

  upcoming_shows = db.session.query(Show.artist_id, Artist.name.label("artist_name"), \
                    Artist.image_link.label("artist_image_link"), \
                    Show.start_time) \
                    .join(Artist, Show.artist_id == Artist.id) \
                    .join(Venue, Show.venue_id == Venue.id) \
                    .filter(Show.start_time >= datetime.utcnow()) \
                    .filter(Show.venue_id == venue_id) \
                    .all()
  
  past_shows_count = len(past_shows)
  upcoming_shows_count = len(upcoming_shows)

  data = Venue.query.get(venue_id)
  
  # Apparently Python allows you to add fields to 
  # an object dynamically (at runtime)
  # https://rosettacode.org/wiki/Add_a_variable_to_a_class_instance_at_runtime#Python
  data.past_shows = past_shows
  data.upcoming_shows = upcoming_shows
  data.upcoming_shows_count = upcoming_shows_count
  data.past_shows_count = past_shows_count

  data.genres = data.genres[1:-1].split(",")
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # Done: insert form data as a new Venue record in the db, instead
  # Done: modify data to be the data object returned from db insertion? Not Sure
  form = VenueForm()
  if not form.validate():
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    return render_template('forms/new_venue.html', form=form)
  
  error = False 

  newVenue = Venue(
    name = form.name.data,
    city = form.city.data,
    state = form.state.data,
    address = form.address.data,
    genres = form.genres.data,
    phone = form.phone.data,
    image_link = form.image_link.data,
    facebook_link = form.facebook_link.data,
    website = form.website.data,
    seeking_talent =  form.seeking_talent.data,
    seeking_description = form.seeking_description.data
  )
  
  venue_id = 1

  try:        
      db.session.add(newVenue)
      db.session.commit()
      venue_id = newVenue.id
  except:
      db.session.rollback()
      error=True        
      print(sys.exc_info())
  finally:
      db.session.close()

  if error:
    # Done: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    return render_template('forms/new_venue.html', form=form)
  else:
    flash('Venue ' + form.name.data + ' was successfully listed!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Delete Venue
#  ----------------------------------------------------------------
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # Done: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  check_venue_exist(venue_id)
  venue = Venue.query.get(venue_id)
  error = False
  try:        
      db.session.delete(venue)
      db.session.commit()
  except:
      db.session.rollback()
      error=True        
      print(sys.exc_info())
  finally:
      db.session.close()
      
  if error:
    abort(422)

  return jsonify({'status': "success"})


#  Update Venue
#  ----------------------------------------------------------------
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  check_venue_exist(venue_id)
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue) 

  # Since generes are stored with curly braces, 
  # I remove them and make a list from them 
  # This is needed to properly display them in edit_artist
  genres = venue.genres[1:-1].split(",")
  form.genres.data = genres
  
  # Done: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  check_venue_exist(venue_id)
  # Done: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get(venue_id)
  form = VenueForm()
  if not form.validate():
    flash('An error occurred. Venue ' + form.name.data + ' could not be updated.')
    return render_template('forms/edit_venue.html', form=form, venue=venue)
  
  error = False 

  venue.name = form.name.data
  venue.city = form.city.data
  venue.state = form.state.data
  venue.address = form.address.data
  venue.genres = form.genres.data
  venue.phone = form.phone.data
  venue.image_link = form.image_link.data
  venue.facebook_link = form.facebook_link.data
  venue.website = form.website.data
  venue.seeking_talent =  form.seeking_talent.data
  venue.seeking_description = form.seeking_description.data
  
  try:        
      db.session.commit()
  except:
      db.session.rollback()
      error=True        
      print(sys.exc_info())
  finally:
      db.session.close()

  if error:
    # Done: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Venue ' + form.name.data + ' could not be updated.')
    return render_template('forms/edit_venue.html', form=form, venue=venue)
  else:
    flash('Venue ' + form.name.data + ' was successfully updated!')

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # Done: replace with real data returned from querying the database
  data = db.session.query(Artist.id, Artist.name)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # Done: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  # As seen in https://stackoverflow.com/questions/3325467/sqlalchemy-equivalent-to-sql-like-statement
  tag = request.form["search_term"]
  search = "%{}%".format(tag)
  artists = db.session.query(Artist.id, Artist.name, db.func.count(Show.artist_id) \
          .filter(Show.start_time > datetime.utcnow()) \
          .label("num_upcoming_shows")) \
          .filter(Artist.name.ilike(search)) \
          .outerjoin(Show, Artist.id == Show.artist_id) \
          .group_by(Artist.id, Artist.name).all()

  response={
    "count": len(artists),
    "data": artists
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  check_artist_exist(artist_id)
  # shows the artist page with the given artist_id
  # Done: replace with real venue data from the venues table, using venue_id
  past_shows =  db.session.query(Show.venue_id, Venue.name.label("venue_name"), \
                    Venue.image_link.label("venue_image_link"), \
                    Show.start_time) \
                    .join(Venue, Show.venue_id == Venue.id) \
                    .join(Artist, Show.artist_id == Artist.id) \
                    .filter(Show.start_time < datetime.utcnow()) \
                    .filter(Show.artist_id == artist_id) \
                    .all()

  upcoming_shows = db.session.query(Show.venue_id, Venue.name.label("venue_name"), \
                    Venue.image_link.label("venue_image_link"), \
                    Show.start_time) \
                    .join(Venue, Show.venue_id == Venue.id) \
                    .join(Artist, Show.artist_id == Artist.id) \
                    .filter(Show.start_time >= datetime.utcnow()) \
                    .filter(Show.artist_id == artist_id) \
                    .all()
  
  past_shows_count = len(past_shows)
  upcoming_shows_count = len(upcoming_shows)

  data = Artist.query.get(artist_id)
  
  # Apparently Python allows you to add fields to 
  # an object dynamically (at runtime)
  # https://rosettacode.org/wiki/Add_a_variable_to_a_class_instance_at_runtime#Python
  data.past_shows = past_shows
  data.upcoming_shows = upcoming_shows
  data.upcoming_shows_count = upcoming_shows_count
  data.past_shows_count = past_shows_count

  data.genres = data.genres[1:-1].split(",")
  
  return render_template('pages/show_artist.html', artist=data)

#  Delete Venue
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  check_artist_exist(artist_id)
  # Done: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete an Artist on a Artist Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  artist = Artist.query.get(artist_id)
  error = False
  try:        
      db.session.delete(artist)
      db.session.commit()
  except:
      db.session.rollback()
      error=True        
      print(sys.exc_info())
  finally:
      db.session.close()
      
  if error:
    abort(422)

  return jsonify({'status': "success"})

#  Update Artist
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  check_artist_exist(artist_id)
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist) 

  # Since generes are stored with curly braces, 
  # I remove them and make a list from them 
  # This is needed to properly display them in edit_artist
  genres = artist.genres[1:-1].split(",")
  form.genres.data = genres
  
  # Done: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  check_artist_exist(artist_id)
  # Done: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist = Artist.query.get(artist_id)
  form = ArtistForm()
  if not form.validate():
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
    print(form.errors)
    return render_template('forms/edit_artist.html', form=form, artist=artist)
  
  error = False

  artist.name = form.name.data
  artist.city = form.city.data
  artist.state = form.state.data
  artist.phone = form.phone.data
  artist.genres = form.genres.data
  artist.image_link = form.image_link.data
  artist.facebook_link = form.facebook_link.data
  artist.website = form.website.data
  artist.seeking_venue = form.seeking_venue.data
  artist.seeking_description = form.seeking_description.data

  try:        
      db.session.commit()
  except:
      db.session.rollback()
      error=True        
      print(sys.exc_info())
  finally:
      db.session.close()
      
  if error:
    # Done: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Artist ' + form.name.data + ' could not be updated.')
    return render_template('forms/edit_artist.html', form=form, artist=artist)
  else:
    # on successful db insert, flash success
    flash('Artist ' + form.name.data + ' was successfully updated!')
  return redirect(url_for('show_artist', artist_id=artist_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # Done: insert form data as a new Artist record in the db, instead
  # Done: modify data to be the data object returned from db insertion? Not Sure
  form = ArtistForm()
  if not form.validate():
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
    print(form.errors)
    return render_template('forms/new_artist.html', form=form)
  
  error = False

  newArtist = Artist(
    name = form.name.data,
    city = form.city.data,
    state = form.state.data,
    phone = form.phone.data,
    genres = form.genres.data,
    image_link = form.image_link.data,
    facebook_link = form.facebook_link.data,
    website = form.website.data,
    seeking_venue = form.seeking_venue.data,
    seeking_description = form.seeking_description.data
  )
  artist_id = 1
  try:        
      db.session.add(newArtist)
      db.session.commit()
      artist_id = newArtist.id
  except:
      db.session.rollback()
      error=True        
      print(sys.exc_info())
  finally:
      db.session.close()
      
  if error:
    # Done: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
    return render_template('forms/new_artist.html', form=form)
  else:
    # on successful db insert, flash success
    flash('Artist ' + form.name.data + ' was successfully listed!')
  return redirect(url_for('show_artist', artist_id=artist_id))
  #return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # Done: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  data = db.session.query(Show.venue_id.label("venue_id"), Venue.name.label("venue_name"), \
                           Show.artist_id.label("artist_id"), Artist.name.label("artist_name"), \
                           Artist.image_link.label("artist_image_link"),
                           Show.start_time) \
                           .join(Venue, Venue.id == Show.venue_id) \
                           .join(Artist, Artist.id == Show.artist_id) \
                           .filter(Show.start_time >= datetime.utcnow()) \
                           .order_by(Show.start_time.asc()).all()

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # Done: insert form data as a new Show record in the db, instead
  form = ShowForm()
  if not form.validate():
    flash('An error occurred. Show could not be listed.')
    print(form.errors)
    return render_template('forms/new_show.html', form=form)
  
  error = False

  newShow = Show(
    venue_id = form.venue_id.data,
    artist_id = form.artist_id.data,
    start_time = form.start_time.data
  )
  
  try:        
      db.session.add(newShow)
      db.session.commit()
  except:
      db.session.rollback()
      error=True        
      print(sys.exc_info())
  finally:
      db.session.close()
      
  if error:
    # Done: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Show could not be listed.')
    return render_template('forms/new_show.html', form=form)
  else:
    # on successful db insert, flash success
    flash('Show was successfully listed!')

  return redirect(url_for('shows'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Utils.
#----------------------------------------------------------------------------#
def check_venue_exist(venue_id):
  venue_exists = db.session.query(Venue.id).filter_by(id=venue_id).first() is not None
  if not venue_exists:
    abort(404)

def check_artist_exist(artist_id):
  artist_exists = db.session.query(Artist.id).filter_by(id=artist_id).first() is not None
  if not artist_exists:
    abort(404)

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
