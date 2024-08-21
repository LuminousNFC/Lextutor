# PoC MasterLaw (Lextutor Project)

Ce projet utilise FastAPI pour l'analyse juridique.

This project implements a FastAPI application for legal analysis.

## Improvements Made
- Enhanced error handling for better user feedback.
- Optimized caching strategy using cachetools.
- Refactored code for better organization with utility functions.
- Improved documentation and comments throughout the code.

## Getting Started

To run this application, follow these steps:

1. Ensure you have Python 3.8+ installed on your system.

2. Clone this repository:
   ```
   git clone [repository-url]
   cd agent-zero/work_dir/Lextutor
   ```

3. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Set up your environment variables:
   Create a `.env` file in the root directory and add the following:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

6. Run the application:
   ```
   uvicorn app.main:app --reload
   ```

7. Open your browser and navigate to `http://localhost:8000` to access the application.

## Testing

To run the tests, execute the following command:
```
pytest
```

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests to us.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.
