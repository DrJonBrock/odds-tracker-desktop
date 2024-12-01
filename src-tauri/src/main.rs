#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

// Import necessary components for handling web requests and Tauri commands
use tauri::command;
use reqwest::header::{HeaderMap, HeaderValue, USER_AGENT};

// This function will be callable from our frontend JavaScript
#[command]
async fn fetch_odds(url: String) -> Result<String, String> {
    // Create a new HTTP client
    let client = reqwest::Client::new();
    
    // Set up headers to make our request look like it's coming from a web browser
    let mut headers = HeaderMap::new();
    headers.insert(USER_AGENT, HeaderValue::from_static(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ));
    
    // Make the HTTP request with our configured headers
    let response = client
        .get(url)
        .headers(headers)
        .send()
        .await
        .map_err(|e| e.to_string())?;
        
    // Get the response text
    let text = response
        .text()
        .await
        .map_err(|e| e.to_string())?;
        
    Ok(text)
}

fn main() {
    // Set up the Tauri application with our fetch_odds command
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![fetch_odds])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}