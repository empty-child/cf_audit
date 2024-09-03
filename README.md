# OSM Conflation Audit

This website takes a JSON output from [OSM Conflator](https://github.com/mapsme/osm_conflate)
and presents logged-in users an interface for validating each imported point, one-by-one.
It records any changes and produces a file that can be later feeded back to the Conflator.

## Author and License

The original version of the auditor was written by Ilya Zverev for MAPS.ME. 
Further development was carried out by Geometalab.

Published under Apache License 2.0.

## Running using docker-compose

You can run this project locally (or using an adapted version on your server as well) 
using the provided docker-compose file.

1. Create an application 

   * Create new application on `https://www.openstreetmap.org/oauth2/applications`, 
   clicking by `Register new application` button
   * Add the name what you want, add `https://localhost:8080/oauth` as redirect URL 
   and check `Read user preferences` permission 
   * Register it
   * Copy `Client ID` and `Client Secret` from form

   *Make sure to use the OAuth2, it's the only one available today option to operate OSM API* 

1. Create a secure key for the secret key: `openssl rand -hex 32` (which 
should be different on every deployment, expecially in production!)

1. Copy the `.env-dist` file to `.env` and enter your keys (`Client ID` and `Client Secret` respectively) as follows:

   ```
   CLIENT_ID=<Client ID from the first step>
   CLIENT_SECRET=<Client Secret from the first step>
   SECRET_KEY=<Key from the previous step>
   ```

1. To host securely, create a certificate for the auditor. For localhost, 
   you can use [mkcert](https://github.com/FiloSottile/mkcert). Enter
   `mkcert localhost` and copy to the root folder. By default,
   auditor awaits `cert.crt` and `cert.key` files. But you can
   change names or/and path in `docker/Dockerfile`

1. Then start it on your machine using docker-compose: `cd docker && docker-compose up --build`.

1. Open your browser at `https://localhost:8080` and start using it.

*Remember that by default you only have the user role. You need either to
add users' ids **(not username!)** in `ADMINS`, separated by a comma `,` 
(i.e. `ADMINS=1234,98765`), or set the flag `EVERY_ONE_IS_ADMIN=1` in `.env` file. 
User ID by username can be requested [here](https://whosthat.osmz.ru/)*
