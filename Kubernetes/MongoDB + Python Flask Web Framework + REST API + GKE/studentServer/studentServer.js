const http = require('http');
const url = require('url');
const { MongoClient } = require('mongodb');
const { MONGO_URL, MONGO_DATABASE } = process.env;
// Connection URI
const uri = mongodb://${MONGO_URL}/${MONGO_DATABASE};
console.log(uri);

// Create a server
const server = http.createServer(async (req, res) => {
  try {
    // Parse the URL and query string
    const parsedUrl = url.parse(req.url, true);
    const student_id = parseInt(parsedUrl.query.student_id);

    // Match req.url with the string /api/score
    if (/^\/api\/score/.test(req.url)) {
      // Connect to the database
      const client = new MongoClient(uri);
      await client.connect();
      const db = client.db("studentdb");

      // Find the student document
      const student = await db.collection("students").findOne({ "student_id": student_id });
      await client.close();

      if (student) {
        // Prepare the response object
        const response = {
          student_id: student.student_id,
          student_name: student.student_name,
          student_score: student.grade
        };

        // Send the response
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(response) + '\n');
      } else {
        res.writeHead(404);
        res.end("Student Not Found\n");
      }
    } else {
      res.writeHead(404);
      res.end("Wrong URL, please try again\n");
    }
  } catch (err) {
    console.error(err);
    res.writeHead(500);
    res.end("Internal Server Error\n");
  }
});

// Start the server
server.listen(8080, () => {
  console.log('Server is listening on port 8080');
});
