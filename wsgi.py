from game import app
import os

if __name__ == "__main__":
    # This block is executed when the script is run directly, not when imported as a module.
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)