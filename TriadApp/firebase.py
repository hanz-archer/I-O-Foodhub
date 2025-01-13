from django.shortcuts import render, redirect
import pyrebase
import json






firebase_config = {
  "apiKey": "AIzaSyCiitL1bVxlZN1_UzLjzQDP_wFY2Ne6OQQ",
  "authDomain": "kentrix-661ce.firebaseapp.com",
  "databaseURL": "https://kentrix-661ce-default-rtdb.asia-southeast1.firebasedatabase.app",
  "projectId": "kentrix-661ce",
  "storageBucket": "kentrix-661ce.firebasestorage.app",
 "messagingSenderId": "563679057431",
  "appId": "1:563679057431:web:56116330f89f74ff17ee52",
  "measurementId": "G-TD1MER6CG9"
}



firebase = pyrebase.initialize_app(firebase_config)
database = firebase.database()
auth = firebase.auth()