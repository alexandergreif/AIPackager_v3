"""Route handlers for AIPackager v3."""

from flask import Flask


def register_routes(app: Flask) -> None:
    """Register all application routes.

    Args:
        app: Flask application instance
    """

    @app.route("/upload")
    def upload():
        """File upload page."""
        return """
        <html>
        <head><title>Upload - AIPackager</title></head>
        <body>
            <h1>Upload Installer</h1>
            <p>Upload your Windows installer file (MSI/EXE) to generate PSADT script.</p>
            <form>
                <input type="file" name="installer" accept=".msi,.exe">
                <button type="submit">Upload</button>
            </form>
        </body>
        </html>
        """

    @app.route("/progress/<id>")
    def progress(id: str):
        """Progress tracking page."""
        return f"""
        <html>
        <head><title>Progress - AIPackager</title></head>
        <body>
            <h1>Processing Progress</h1>
            <p>Job ID: {id}</p>
            <div>Progress: Processing your installer...</div>
            <div>Status: In Progress</div>
        </body>
        </html>
        """

    @app.route("/detail/<id>")
    def detail(id: str):
        """Result details page."""
        return f"""
        <html>
        <head><title>Details - AIPackager</title></head>
        <body>
            <h1>Job Details</h1>
            <p>Job ID: {id}</p>
            <div>
                <h2>Generated PSADT Script</h2>
                <p>Your PowerShell App Deployment Toolkit script is ready.</p>
                <textarea rows="10" cols="80">
# Generated PSADT Script for Job {id}
# This is a placeholder script
                </textarea>
            </div>
        </body>
        </html>
        """

    @app.route("/history")
    def history():
        """Upload history page."""
        return """
        <html>
        <head><title>History - AIPackager</title></head>
        <body>
            <h1>Upload History</h1>
            <table border="1">
                <tr>
                    <th>Job ID</th>
                    <th>Filename</th>
                    <th>Status</th>
                    <th>Created</th>
                </tr>
                <tr>
                    <td>sample-001</td>
                    <td>example.msi</td>
                    <td>Complete</td>
                    <td>2025-06-21</td>
                </tr>
            </table>
        </body>
        </html>
        """
