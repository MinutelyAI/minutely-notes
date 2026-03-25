// Copy this file to config.js and fill in your actual keys
// config.js is gitignored — never commit it

const CONFIG = {
  // Deepgram API key (https://console.deepgram.com)
  DEEPGRAM_KEY: "YOUR_DEEPGRAM_API_KEY",

  // Modal transcription endpoint (from: modal deploy modal_app.py)
  MODAL_URL: "https://YOUR_MODAL_APP.modal.run",

  // Firebase config (https://console.firebase.google.com)
  FIREBASE: {
    apiKey: "YOUR_FIREBASE_API_KEY",
    authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
    databaseURL: "https://YOUR_PROJECT_ID-default-rtdb.firebaseio.com",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_PROJECT_ID.firebasestorage.app",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_FIREBASE_APP_ID"
  }
};
