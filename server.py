from flask import Flask, jsonify, request, send_file
import nexradaws
import os
import logging
from flasgger import Swagger, swag_from
from ingestor import save_file
from merra import SessionWithHeaderRedirection, download_nc4
from datetime import date
from message_queue import init_rabbitmq

# pylint: disable=unused-argument
def create_app(test_config=None):

    conn = nexradaws.NexradAwsInterface()

    # create session with the user credentials that will be used to authenticate access to the data
    username = os.environ.get("NASA_USERNAME")
    password = os.environ.get("NASA_PASSWORD")

    if username and password:
        session = SessionWithHeaderRedirection(username, password)
    else:
        raise SystemExit("Credentials for earthdata not set")

    app = Flask(__name__)

    try:
        init_rabbitmq(session)
    except Exception as e:
        logging.exception(f"Rabbit MQ not initialized {str(e)}")
        raise SystemExit

    template = {
      "swagger": "2.0",
      "info": {
        "title": "Ingestor API",
        "description": "Endpoints available with Ingestor",
        "contact": {
          "responsibleOrganization": "dexlab",
          "responsibleDeveloper": "Shubham Thakur",
          "email": "sdthakur@iu.edu",
          "url": "https://github.com/airavata-courses/dexlab/tree/ingestor",
        },
        "version": "0.0.1"
      }
    }

    Swagger(app, template=template)

    def split_date(date):
        date = date.split('-')
        return date[0], date[1], date[2]

    @app.route('/merra', methods=["GET"])
    @swag_from('nasa_plot.yml')
    def merra():
        args = request.args
        print(args.get("month"))
        print(args.get("year"))
        month = args.get("month")

        if month:
            try:
                month_val = int(month)
            except ValueError:
                #raise ValueError('date', 'Invalid month')
                return 'Invalid month', 400

            if month_val > 12:
                #raise ValueError('date', 'Invalid year or month')
                return 'Invalid month', 400

            if len(month) == 1:
                month = '0' + month
        else:
            #raise ValueError('date', 'Invalid year or month')
            return 'Invalid month', 400

        year = args.get("year")

        if year:
            try:
                year_val = int(year)
            except ValueError:
                #raise ValueError('date', 'Invalid year')
                return 'Invalid year', 400

            if year_val < 1981 or year_val > date.today().year:
                #raise ValueError('date', 'Invalid year')
                return 'Invalid year', 400
        else:
            #raise ValueError('date', 'Invalid year')
            return 'Invalid year', 400

        year = args.get("year")
        plot_type = args.get("plot_type")

        try:
            plot_file = download_nc4(session, year, month, plot_type)
        except ValueError as err:
            err_type, err_message = err.args
            return err_message, 400

        return send_file(plot_file, as_attachment=False)

    @app.route('/radars', methods=["POST"])
    @swag_from('radar.yml')
    def get_radars():

        """
        radar_list = ['1','2']
        response = {
                'radars': radar_list
        }
        return jsonify(response)
        """

        body = request.get_json(force=True)
        try:
            date = body['date']
            year, month, day = split_date(date)
        except KeyError:
            return "date key must be present", 400

        radar_list = conn.get_avail_radars(year, month, day)

        response = {
                'radars': radar_list
        }

        return jsonify(response)

    @app.route('/plot', methods=['POST'])
    @swag_from('plot.yml')
    def get_plot():
        body = request.get_json(force=True)

        try:
            date = body['date']
            year, month, day = split_date(date)
            radar = body['radar']
        except KeyError:
            return "date and radar must be part of the body", 400

        file = save_file(conn, year, month, day, radar)
        return send_file(file, as_attachment=False)

    return app
