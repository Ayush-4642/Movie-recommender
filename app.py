from flask import Flask, render_template, request
import pandas as pd
from fuzzywuzzy import fuzz

app = Flask(__name__)

# Load and clean dataset
df = pd.read_csv("IMDb Movies India.csv", encoding="latin1")
df = df.dropna(subset=["Name"])
df["Name"] = df["Name"].str.strip().str.lower()

# Genre icon mapping
def genre_with_icon(genre):
    genre = genre.lower()
    icons = {
        "drama": "🎭",
        "comedy": "😂",
        "thriller": "😱",
        "action": "🔥",
        "romance": "❤️",
        "musical": "🎶",
        "crime": "🕵️",
        "horror": "👻",
        "sci-fi": "🚀",
        "fantasy": "🧙"
    }
    return f"{icons.get(genre, '🎬')} {genre.capitalize()}"

# Recommendation function
def recommend_content(movie_name):
    movie_name = movie_name.strip().lower()
    print("🔍 Searching for:", movie_name)

    # Compute fuzzy similarity scores
    df["score"] = df["Name"].apply(lambda x: fuzz.partial_ratio(movie_name, x))

    # Sort by score and take top 5
    top_matches = df.sort_values(by="score", ascending=False).head(5)

    print("🎯 Matches found:", top_matches["Name"].tolist())

    if top_matches.empty or top_matches["score"].max() < 40:
        return [{"Name": "Movie not found.", "Genre": ""}]

    recommendations = []
    for _, row in top_matches.iterrows():
        genre_raw = str(row["Genre"]) if pd.notna(row["Genre"]) else ""
        genre_list = genre_raw.split(",")
        genre_icons = ", ".join([genre_with_icon(g.strip()) for g in genre_list])
        recommendations.append({"Name": row["Name"], "Genre": genre_icons})

    return recommendations

@app.route("/", methods=["GET", "POST"])
def index():
    recommendations = []
    if request.method == "POST":
        movie_name = request.form.get("movie", "").split(" - ")[0].strip().lower()
        try:
            recommendations = recommend_content(movie_name)
        except Exception as e:
            print("⚠️ Error in index route:", e)
            recommendations = [{"Name": "Movie not found.", "Genre": ""}]

    # ✅ Homepage no longer dumps all movies, just passes recommendations
    return render_template("index.html", recommendations=recommendations)

# ✅ Step 2: Dedicated route for full movie list with pagination
@app.route("/movies")
def movies():
    page = int(request.args.get("page", 1))
    per_page = 50  # number of movies per page
    start = (page - 1) * per_page
    end = start + per_page

    all_movies = []
    for _, row in df.sort_values(by="Name").iloc[start:end].iterrows():
        genre_raw = str(row["Genre"]) if pd.notna(row["Genre"]) else ""
        genre_list = genre_raw.split(",")
        genre_icons = ", ".join([genre_with_icon(g.strip()) for g in genre_list])
        all_movies.append({"Name": row["Name"], "Genre": genre_icons})

    total_movies = len(df)
    total_pages = (total_movies // per_page) + (1 if total_movies % per_page else 0)

    return render_template("movies.html", all_movies=all_movies, page=page, total_pages=total_pages)

@app.route("/autocomplete")
def autocomplete():
    query = request.args.get("q", "").strip().lower()
    df["score"] = df["Name"].apply(lambda x: fuzz.partial_ratio(query, x))
    matches = df.sort_values(by="score", ascending=False).head(10)
    suggestions = [f"{row['Name']} - {row['Genre']}" for _, row in matches.iterrows()]
    return {"suggestions": suggestions}

if __name__ == "__main__":
    app.run(debug=True)