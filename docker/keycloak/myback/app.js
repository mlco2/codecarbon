/*
 * JBoss, Home of Professional Open Source
 * Copyright 2016, Red Hat, Inc. and/or its affiliates, and individual
 * contributors by the @authors tag. See the copyright.txt in the
 * distribution for a full listing of individual contributors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

var express = require('express');
var session = require('express-session');
var bodyParser = require('body-parser');
var Keycloak = require('keycloak-connect');
var cors = require('cors');
var request = require('request');

var Token = require('./node_modules/keycloak-connect/middleware/auth-utils/token.js');

var app = express();
app.use(bodyParser.json());

// Enable CORS support
app.use(cors());

// Create a session-store to be used by both the express-session
// middleware and the keycloak middleware.

var memoryStore = new session.MemoryStore();

app.use(session({
  secret: 'some secret',
  resave: false,
  saveUninitialized: true,
  store: memoryStore
}));

// Provide the session store to the Keycloak so that sessions
// can be invalidated from the Keycloak console callback.
//
// Additional configuration is read from keycloak.json file
// installed from the Keycloak web console.

var keycloak = new Keycloak({
  store: memoryStore
});

app.use(keycloak.middleware({
  logout: '/logout',
  admin: '/'
}));

app.get('/service/public', function (req, res) {
  res.json({ message: 'public' });
});

app.get('/service/secured', keycloak.protect('realm:user'), function (req, res) {
  res.json({ message: 'secured' });
});

app.get('/service/admin', keycloak.protect('realm:adminuser'), function (req, res) {
  res.json({ message: 'admin' });
});

function pants(token, request) {
  var token = new Token(request.headers.authorization.substring(7), keycloak.config.clientId);
  return token.hasRole('realm:user') || token.hasRole('realm:admin');
  //return token.hasRole('moderator');
  //return token.hasRole('myback:moderator');
};

app.get('/service/getAccount', keycloak.protect(pants), function (req, res) {
  // Retrieve token from request header
  var token = new Token(req.headers.authorization.substring(7), keycloak.config.clientId);

  keycloak.grantManager.userInfo(token).then(function (value) {
    res.json({
      message: 'getAccount',
      userInfo: value
    });
  });

});

app.get('/service/validateToken', keycloak.protect(), function (req, res) {
  // Retrieve token from request header
  var token = new Token(req.headers.authorization.substring(7), keycloak.config.clientId);
  // Validate Token
  keycloak.grantManager.validateToken(token, 'Bearer').then(function (value) {
    res.json({
      message: 'validateToken',
      validateToken: value
    });
  });

});

app.get('/service/getUsers', keycloak.protect(), function (req, res) {
  // Obtain an access Token
  keycloak.grantManager.obtainFromClientCredentials().then(function (value) {
    // use API to get all users
    request({
      url: keycloak.config.realmAdminUrl + '/users',
      method: 'GET',
      headers: {
        'Authorization': 'Bearer ' + value.access_token.token
      }
    }, function (error, response, body) {
      if (!error && response.statusCode == 200) {
        const info = JSON.parse(body);
        res.send(info);
      } else {
        console.log(response.statusCode);
      }
    });
  });
});


app.use('*', function (req, res) {
  res.send('Not found!');
});

app.listen(3000, function () {
  console.log('Started at port 3000');
});
