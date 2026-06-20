import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

// Public web config for the Firebase project "warmth-gtm-hackathon".
// These values are safe to expose in client code; access is controlled by
// Firebase Auth + Firestore security rules. Override via VITE_FIREBASE_* env.
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY ?? "AIzaSyBXPuw7x_FvMB3y-hBf6Rfzwpr3S7LHP2Q",
  authDomain:
    import.meta.env.VITE_FIREBASE_AUTH_DOMAIN ?? "warmth-gtm-hackathon.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID ?? "warmth-gtm-hackathon",
  storageBucket:
    import.meta.env.VITE_FIREBASE_STORAGE_BUCKET ??
    "warmth-gtm-hackathon.firebasestorage.app",
  messagingSenderId:
    import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID ?? "30164818817",
  appId:
    import.meta.env.VITE_FIREBASE_APP_ID ??
    "1:30164818817:web:e091ea2ebd55ee8cf2e680",
};

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

/** Force Google account picker on every sign-in (not silent re-auth). */
export function googleSignInProvider() {
  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: "select_account" });
  return provider;
}
