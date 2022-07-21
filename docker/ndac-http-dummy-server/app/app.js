const express = require("express");
const bodyParser = require("body-parser");
const server = express();
const get_data = require('./access-point-sims.json')
const post_data = require('./iccids-sims.json');

//Here we are configuring express to use body-parser as middleware.
server.use(bodyParser.urlencoded({ extended: true }));
server.use(bodyParser.json());

server.get('/api/ndac/v2/access-point-sims', (req, res) => {
  const url = req.url;
  const status = res.statusCode
  console.log(req.method+" "+url+" "+status);
  if (status == 200) {
    // Print JSON content
    res.json(get_data);
  }
})

server.post('/api/ndac/v2/iccids-sims',(req, res) => {
  const url = req.url;
  const status = res.statusCode;
  var body = req.body;
  console.log(req.method+" "+url+" "+status);
  console.log("Request body:", body)
  if (status == 200) {
    // Print JSON content
    res.json(post_data);
  }  
});

server.listen(3000, () => {
  console.log("JSON Server is running");
});