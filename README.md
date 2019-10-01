<img src="https://raw.githubusercontent.com/bbrause/subrosa/master/img/subrosa_logo.png" alt="SUB ROSA" title="SUB ROSA" height="120" align="left">
SUB ROSA

subtitle-based film similarities  

<img src="https://img.shields.io/github/license/bbrause/subrosa?color=Lightgray"/> <img src="https://img.shields.io/github/last-commit/bbrause/subrosa?color=Lightgray"/> 
----

Do similar films use a similar language? SUB ROSA addresses this question by giving users the ability to examine movies for  speech-related features. These features are extracted from subtitle data using methods from Natural Language Processing, Stylometry and Information Retrieval.  
For detailed information about these methods, please read this [paper](https://github.com/bbrause/subrosa/raw/master/Luhmann_2019_MovieSimilarities.pdf).   

This work was realized by Jan Luhmann as part of the course ”Drama Mining und Film-Analyse” (summer semester 2019) under the supervision of Manuel Burghardt and Jochen Tiepmar at the University of Leipzig.  

Subtitle data was kindly provided by the team of <a href="http://www.opensubtitles.org" target="_blank">OpenSubtitles.  
<a href="http://www.opensubtitles.org" target="_blank"><img src="https://raw.githubusercontent.com/bbrause/subrosa/master/img/opensubtitles_logo.png" title="OpenSubtitles" height="120"/></a>
  
----
  
### Installation

1. Make sure you have Python 3 installed. Also install dependencies using `pip`:
```
pip install Flask numpy scikit-learn 
```
2. Clone this repository.
```
git clone https://github.com/bbrause/subrosa.git
```
3. Move to the repository folder and start the app.
```
cd subrosa
python3 app/app.py
```
