import streamlit as st  # To create main app.
import pickle  # To save the model.
import pandas as pd  # To create dataframe.
import requests  # To get the request.

movies_dic = pickle.load(open('movies_dic.pkl', 'rb'))  # To open save model.
movies = pd.DataFrame(movies_dic)

similarity = pickle.load(open('tag_similarity.pkl', 'rb'))  # To open the saved model.

def fetch_poster(movie_id):
    """This function use api to get the response and return the poster"""
    reponse = requests.get("https://api.themoviedb.org/3/movie/{}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US".format(movie_id))
    data = reponse.json()
    print(data)
    return "https://image.tmdb.org/t/p/w500" + data['poster_path']

def recommendation(movie):
    """This function fetches the title and poster using the index."""
    index = movies[movies['title'] == movie].index[0]
    distance = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda vector: vector[1])

    movies_recommended = []
    movies_recommended_poster = []
    for dist in distance[0:5]:
        movie_id = movies.iloc[dist[0]].id
        movies_recommended.append(movies.iloc[dist[0]].title)
        movies_recommended_poster.append((fetch_poster(movie_id)))
    return movies_recommended, movies_recommended_poster

st.title('AI-Powered Movie Recommender System')

select_movie = st.selectbox("What's in your mind", (movies['title'].values))

# creating a button for name and poster
if st.button('Recommend'):
    names, posters = recommendation(select_movie)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.text(names[0])
        st.image(posters[0])

    with col2:
        st.text(names[1])
        st.image(posters[1])

    with col3:
        st.text(names[2])
        st.image(posters[2])


    col4, col5, col6 = st.columns(3)

    if len(names) > 3:
        with col4:
            st.text(names[3])
            st.image(posters[3])

    if len(names) > 4:
        with col5:
            st.text(names[4])
            st.image(posters[4])