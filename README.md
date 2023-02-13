# OSM Conflation Audit

This website takes a JSON output from [OSM Conflator](https://github.com/mapsme/osm_conflate)
and presents logged-in users an interface for validating each imported point, one-by-one.
It records any changes and produces a file that can be later feeded back to the Conflator.

## Author and License

All this was written by Ilya Zverev for MAPS.ME. Published under Apache License 2.0.

## Running using docker-compose

You can run this project locally (or using an adapted version
on your server as well) using the provided docker-compose file.

1. Create an application (`Register your application` Button) on `https://www.openstreetmap.org/user/<your-osm-user-name>/oauth_clients`
  and use `localhost:8080` as your main application URL. Make sure to use the OAuth1 settings.

1. Copy the `.env-dist` file to `.env` and enter your keys (the "Consumer Key" respectively the "Consumer Secret") as follows:

    ```bash
    OAUTH_KEY=<your-key>
    OAUTH_SECRET=<your-secret>
    SECRET_KEY=<secret-key-do-not-share>
    MAPILLARY_CLIENT_ID=<mapillary-key-if-any>
    ```

  - to create a secure key for the secret key on linux: `openssl rand -hex 32` (which should be different on every deployment, expecially in production!)

1. Then start it on your machine using docker-compose: `cd docker && docker-compose up --build`.

Open your browser at `localhost:8080` and start using it.

In case you don't have admin-rights, uncomment the line in the `docker-compose.yml` with `# ADMINS: ''`.
You can add multiple admins by separating the values with a comma (`,`), ie. `ADMINS: '1234,98765'`
