  #!/bin/bash

  # Apply database migrations
  flask db init
  flask db migrate
  flask db upgrade

  # Start the Gunicorn server
  gunicorn run:app
