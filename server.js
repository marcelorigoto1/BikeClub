const express = require('express');
const serveIndex = require('serve-index');
const path = require('path');

const app = express();

// Serve static files and enable directory listing
app.use('/data', express.static(path.join(__dirname, 'data')));
app.use('/data', serveIndex(path.join(__dirname, 'data'), { icons: true }));

// Serve the public directory
app.use(express.static(path.join(__dirname)));

const PORT = 8000;
app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});
