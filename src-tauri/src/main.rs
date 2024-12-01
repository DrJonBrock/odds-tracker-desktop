#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::command;
use reqwest::header::{HeaderMap, HeaderValue, USER_AGENT};

#[command]
async fn fetch_odds(url: String) -> Result<String, String> {
    let client = reqwest::Client::new();
    
    let mut headers = HeaderMap::new();
    headers.insert(USER_AGENT, HeaderValue::from_static("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"));
    
    let response = client
        .get(url)
        .headers(headers)
        .send()
        .await
        .map_err(|e| e.to_string())?;
        
    let text = response
        .text()
        .await
        .map_err(|e| e.to_string())?;
        
    Ok(text)
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![fetch_odds])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}