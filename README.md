# AI Medical Scribe 🩺

An AI-powered medical scribe application that converts patient conversations into professional SOAP notes using advanced language models.

## Features

- 🤖 **AI-Powered SOAP Note Generation** - Converts patient interviews into standardized medical records
- 🎨 **Professional Web Interface** - Modern, medical-themed UI with responsive design
- 🔒 **Secure Environment Configuration** - API keys managed through environment variables
- ⚡ **Real-time Processing** - Generate SOAP notes in seconds
- 📱 **Mobile Responsive** - Works seamlessly on all devices

## Live Demo

🚀 **[View Live Application](https://your-vercel-url.vercel.app)**

## Quick Start

### 1. Environment Setup

Copy the environment template and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your actual API keys:
```env
OPENAI_API_KEY=your-openai-api-key-here
HUGGINGFACE_API_KEY=your-huggingface-api-key-here
SECRET_KEY=your-secret-key-here
```

### 2. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Visit `http://localhost:5000` to use the application.

## Deployment

### Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/manueldavidc12/ai-medical-scribe)

1. **Fork this repository**
2. **Connect to Vercel** - Import your GitHub repository
3. **Add Environment Variables** in Vercel dashboard:
   - `OPENAI_API_KEY`
   - `HUGGINGFACE_API_KEY`
   - `SECRET_KEY`
4. **Deploy** - Vercel will automatically build and deploy

### Manual Vercel Deployment

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

## API Keys Required

- **OpenAI API Key** - For advanced SOAP note generation
- **Hugging Face API Key** - For medical model inference

## Tech Stack

- **Backend**: Flask, Python 3.9+
- **Frontend**: HTML5, CSS3, JavaScript
- **AI Models**: OpenAI GPT, Hugging Face Transformers
- **Deployment**: Vercel Serverless Functions
- **Styling**: Modern CSS with medical theme

## Project Structure

```
medical-chatbot/
├── app.py                 # Vercel entry point
├── web_chatbot.py         # Main Flask application
├── templates/             # HTML templates
│   ├── landing.html       # Landing page
│   └── index.html         # Chat interface
├── requirements.txt       # Python dependencies
├── vercel.json           # Vercel configuration
└── .env.example          # Environment template
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For support, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ for healthcare professionals**