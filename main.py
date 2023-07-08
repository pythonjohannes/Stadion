from flask import Flask, render_template, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, IntegerField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

WTF_CSRF_SECRET_KEY = 'a random string'
bootstrap = Bootstrap5(app)


app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///all_info-arbetare.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Adam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    namn = db.Column(db.String, unique=True, nullable=False)
    starttid = db.Column(db.Integer)

class AddCommentForm(FlaskForm):
    kommentar = StringField(validators=[DataRequired()])
    posta_kommentar = SubmitField("Lägg till kommentar")
    id = IntegerField(validators=[DataRequired()])

class Johannes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    passets_namn = db.Column(db.String, unique=False, nullable=False)
    arbetarens_namn = db.Column(db.String, unique=False, nullable=False)
    starttid_timme = db.Column(db.Integer, nullable=False)
    starttid_minut = db.Column(db.Integer, nullable=False)
    instämplad_timme = db.Column(db.Integer, nullable=True, default="")
    instämplad_minut = db.Column(db.Integer, nullable=True, default="")
    anlänt = db.Column(db.Boolean, unique=False, default=False)
    sluttid_timme = db.Column(db.Integer, nullable=False)
    sluttid_minut = db.Column(db.Integer, nullable=False)
    utstämplad_timme = db.Column(db.Integer, nullable=True, default="")
    utstämplad_minut = db.Column(db.Integer, nullable=True, default="")
    avslutat = db.Column(db.Boolean, unique=False, default=False)
    kommentar = db.Column(db.String, unique=False, nullable=True)

with app.app_context():
   db.create_all()

class TestForm(FlaskForm):
    passet = StringField(validators=[DataRequired()])
    namn = StringField("Arbetare", validators=[DataRequired()])
    timme_start = SelectField("Tid Börja", choices=list(range(0,24)))
    minut_start = SelectField(choices=list(range(0, 60)))
    timme_slut = SelectField("Tid Sluta", choices=list(range(0, 24)))
    minut_slut = SelectField(choices=list(range(0, 60)))
    submit = SubmitField("Lägg till")


@app.route("/")
def hem():
    #Hitta i databasen vad de olika passen heter
    with app.app_context():
        resultat = db.session.execute(db.select(Johannes))
        alla_pass = resultat.scalars()
        lista_pass_namn = []
        for p in alla_pass.unique():
            lista_pass_namn.append(p.passets_namn)
        lista_pass = list(dict.fromkeys(lista_pass_namn))

    return render_template("index.html", lista_pass=lista_pass)

@app.route("/adda", methods=["POST", "GET"])
@app.route("/adda/<passet>", methods=["POST", "GET"])
def adda(passet=None):
    form = TestForm(passet=passet)
    if form.validate_on_submit():
        personer = form.namn.data.split(",")
        for person in personer:
            info = Johannes(
                passets_namn=form.passet.data,
                arbetarens_namn=person,
                starttid_timme=form.timme_start.data,
                starttid_minut=form.minut_start.data,
                sluttid_timme=form.timme_slut.data,
                sluttid_minut=form.minut_slut.data
            )
            db.session.add(info)
        db.session.commit()
        return redirect(url_for("arbetspass", passet=form.passet.data))
    return render_template("addera.html", form=form)

@app.route("/arbetspass/<passet>", methods=["POST", "GET"])
def arbetspass(passet):
    with app.app_context():
        specifika_pass = db.session.execute(db.select(Johannes).where(Johannes.passets_namn == passet)).all()
    #sortera personer utifrån status, dvs om de inte kommit, elr har kommit elr gått
    ej_anlängt = []
    anlänt = []
    avslutat = []
    for passet in specifika_pass:
        if passet[0].avslutat:
            avslutat.append(passet)
        elif passet[0].anlänt:
            anlänt.append(passet)
        else:
            ej_anlängt.append(passet)
    specifika_pass = ej_anlängt+anlänt+avslutat
    return render_template("pass.html", specifika_pass=specifika_pass)

@app.route("/delete/<id>/<passets_namn>")
def delete(id, passets_namn):
    person_att_ta_bort = Johannes.query.get_or_404(id)
    db.session.delete(person_att_ta_bort)
    db.session.commit()
    flash("Personen har tagits bort")
    return redirect(url_for("arbetspass", passet=passets_namn))

@app.route("/addcomment", methods=["POST", "GET"])
def addcomment():
     personens_id = request.form["personens_id"]
     kommentar = request.form["kommentar"]
     passets_namn = request.form["passets_namn"]
     personen = Johannes.query.get_or_404(personens_id)
     personen.kommentar = kommentar
     db.session.commit()
     flash("Kommentaren har lagts till")
     return redirect(url_for("arbetspass", passet=passets_namn))

@app.route("/stämpla_in/<id>", methods=["POST", "GET"])
def stämpla_in(id):
    personen = Johannes.query.get_or_404(id)
    if not personen.anlänt:
        flash_meddelande = "Personen har stämplats in"
    else:
        flash_meddelande = "Instämplingstiden har uppdaterats"
    personen.instämplad_timme = request.form["timme"]
    personen.instämplad_minut = request.form["minut"]
    personen.anlänt = True
    passets_namn = request.form["passets_namn"]
    db.session.commit()
    flash(flash_meddelande)
    return redirect(url_for("arbetspass", passet=passets_namn))

@app.route("/stämpla_ut/<id>", methods=["POST", "GET"])
def stämpla_ut(id):
    personen = Johannes.query.get_or_404(id)
    if not personen.avslutat:
        flash_meddelande = "Personen har stämplats ut"
    else:
        flash_meddelande = "Utstämplingstiden har uppdaterats"
    personen.utstämplad_timme = request.form["timme"]
    personen.utstämplad_minut = request.form["minut"]
    personen.avslutat = True
    passets_namn = request.form["passets_namn"]
    db.session.commit()
    flash(flash_meddelande)
    return redirect(url_for("arbetspass", passet=passets_namn))


#    print("test")
#    pass_att_uppdatera = db.session.execute(db.Select(Johannes).where(Johannes.id==id))
#    pass_att_uppdatera.kommentar = comment_form.kommentar.data
#    db.session.commit()
#    return redirect(url_for("arbetspass", passet=passets_namn))
#    comment_form = AddCommentForm()
#   if comment_form.validate_on_submit():
#       print(comment_form.data)
#       pass_att_uppdatera = Johannes.query.get_or_404(2)
#       pass_att_uppdatera.kommentar = comment_form.kommentar
#       db.session.commit()
#       return render_template("pass.html", specifika_pass=specifika_pass, comment_form=comment_form)

if __name__ == "__main__":
    app.run(debug=True, host='dpg-cikl2itph6eg6kca9egg-a', port=5432)


#anlänt och instämplad. Konsekvens.