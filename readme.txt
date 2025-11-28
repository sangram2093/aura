pip install google-cloud-aiplatform requests
python vertex_end_to_end.py --new-pdf path/to/new.pdf \
  --keyfile keyfile.json --project <PROJECT_ID> --location us-central1 \
  --model gemini-1.5-flash --plantuml-out out.puml
# With old version + publish:
python vertex_end_to_end.py --new-pdf new.pdf --old-pdf old.pdf \
  --keyfile keyfile.json --project <PROJECT_ID> --location us-central1 \
  --publish --confluence-url https://your-domain.atlassian.net/wiki \
  --confluence-space SPACE --confluence-parent 12345 \
  --confluence-user you@domain.com --confluence-token <API_TOKEN>
