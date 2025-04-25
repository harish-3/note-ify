import streamlit as st
from streamlit.components.v1 import html

def flashcard(question, answer, width=300, height=200, theme="blue"):
    # Theme color mappings
    theme_colors = {
        "blue": {
            "front": "linear-gradient(135deg, #6a11cb 0%, #2575fc 100%)",
            "back": "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
            "back_text": "#34495e"
        },
        "green": {
            "front": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
            "back": "linear-gradient(135deg, #f5f7fa 0%, #d4e9d4 100%)",
            "back_text": "#1e5631"
        },
        "purple": {
            "front": "linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%)",
            "back": "linear-gradient(135deg, #f5f7fa 0%, #e0d4f0 100%)",
            "back_text": "#4a00e0"
        },
        "orange": {
            "front": "linear-gradient(135deg, #f12711 0%, #f5af19 100%)",
            "back": "linear-gradient(135deg, #f5f7fa 0%, #f9e8d2 100%)",
            "back_text": "#b7410e"
        },
        "dark": {
            "front": "linear-gradient(135deg, #232526 0%, #414345 100%)",
            "back": "linear-gradient(135deg, #e0e0e0 0%, #bdbdbd 100%)",
            "back_text": "#232526"
        }
    }
    
    # Get colors for selected theme
    colors = theme_colors.get(theme, theme_colors["blue"])
    
    card_html = f"""
    <html>
    <head>
        <style>
            .flip-card {{
                background-color: transparent;
                width: {width}px;
                height: {height}px;
                perspective: 1000px;
                margin: 15px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}

            .flip-card-inner {{
                position: relative;
                width: 100%;
                height: 100%;
                text-align: center;
                transition: transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);
                transform-style: preserve-3d;
                box-shadow: 0 10px 20px rgba(0,0,0,0.15); /* Enhanced shadow */
                cursor: pointer;
            }}

            .flip-card:hover .flip-card-inner {{
                transform: rotateY(180deg);
            }}

            .flip-card-front, .flip-card-back {{
                position: absolute;
                width: 100%;
                height: 100%;
                -webkit-backface-visibility: hidden;
                backface-visibility: hidden;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 18px;
                border-radius: 15px;
                padding: 25px;
                line-height: 1.5;
                box-sizing: border-box;
                overflow: auto;
            }}

            .flip-card-front {{
                background: {colors["front"]}; 
                color: white;
                letter-spacing: 0.5px;
                text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
            }}

            .flip-card-back {{
                background: {colors["back"]}; 
                color: {colors["back_text"]};
                transform: rotateY(180deg);
                border: 1px solid #d1d9e6;
            }}
            
            /* Scrollbar styling for overflow content */
            .flip-card-front::-webkit-scrollbar,
            .flip-card-back::-webkit-scrollbar {{
                width: 6px;
                height: 6px;
            }}
            
            .flip-card-front::-webkit-scrollbar-thumb,
            .flip-card-back::-webkit-scrollbar-thumb {{
                background: rgba(0,0,0,0.2);
                border-radius: 3px;
            }}
        </style>
    </head>
    <body>
        <div class="flip-card">
            <div class="flip-card-inner">
                <div class="flip-card-front">
                    <strong>{question}</strong>
                </div>
                <div class="flip-card-back">
                    {answer}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    html(card_html, height=height + 30)