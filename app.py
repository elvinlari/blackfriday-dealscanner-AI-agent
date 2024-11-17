from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from os import environ, path
from models import *
from scraper.deal_analyzer import DealAnalyzer

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DB_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


# create tables
@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/fetch-offers', methods=['POST'])
def fetch_offers():
    try:
        request_data = request.get_json()
        file_name = request_data['file_name']
        if not file_name:
            return make_response(jsonify({'message': 'file name is required'}), 400)
        desired_rows = request_data['desired_rows']
        if not desired_rows:
            return make_response(jsonify({'message': 'desired rows is required'}), 400)

        file_path = path.join("/app/data", file_name)
        sample_data = DealAnalyzer().read_csv(file_path)
        sample_data_str = "\n".join([",".join(row) for row in sample_data])

        print("\nLaunching team of Agents...\n")
        # Analyze the sample data using the Analyzer Agent
        format_of_result = DealAnalyzer().understand_data_format_agent(sample_data_str)
        print("\n#### Data Format Agent output: ####\n")
        print(format_of_result)

        # Call the analyzer agent
        analysis_result = DealAnalyzer().analysis_agent(format_of_result)
        print("\n#### Analysis Agent output: ####\n")
        print(analysis_result)

        # Check the response and print the result
        custom_function_result = DealAnalyzer().calling_custom_function(analysis_result)
        print("\n#### Custom Function output: ####\n")

        # Set up the output file
        output_file = "/app/data/new_dataset.csv"
        headers = sample_data[0] # Get the headers from the sample data
        # Create output file with headers
        DealAnalyzer().save_to_csv("", output_file, headers)

        batch_size = 10 # Number of rows to generate in each batch
        generated_rows = 0 # Counter to keep track of how many rows have been generated

        # Generate the data in batches until we reach the desired number of rows
        while generated_rows < desired_rows:
            # Calculate how many rows to generate in this batch
            rows_to_generate = min(batch_size, desired_rows - generated_rows)
            # Generate a batch of data using the Generator Agent
            generated_data = DealAnalyzer().final_response_agent(custom_function_result, sample_data_str, num_rows=rows_to_generate)
            # Append the generated data to the output file
            DealAnalyzer().save_to_csv(generated_data, output_file)
            # Update the count of the generated rows
            generated_rows += rows_to_generate
            # Print progress update
            print(f"Generated {generated_rows} rows out of {desired_rows}")

        # Inform the user that the process is complete
        print(f"\nGenerated data has been saved to {output_file}")
        return make_response(jsonify({'message': 'Offers fetched and saved to csv file'}), 200)
    except Exception as e:
        return make_response(jsonify({'message': 'error fetching offers', 'error': str(e)}), 500)


# create a test route
@app.route('/test', methods=['GET'])
def test():
    return make_response(jsonify({'message': 'test route'}), 200)


# create a user
@app.route('/users', methods=['POST'])
def create_user():
    try: 
        data = request.get_json()
        new_user = User(username=data['username'], email=data['email'])
        db.session.add(new_user)
        db.session.commit()
        return make_response(jsonify({'message': 'User created'}), 201)
    except Exception as e:
        return make_response(jsonify({'message': 'error creating user', 'error': str(e)}), 500)
    

# get all users
@app.route('/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        return make_response(jsonify([user.json() for user in users]), 200)
    except Exception as e:
        return make_response(jsonify({'message': 'error getting users', 'error': str(e)}), 500)
    

# get a user by id
@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    try:
        user = User.query.filter_by(id=id).first()
        if user:
            return make_response(jsonify(user.json()), 200)
        return make_response(jsonify({'message': 'User not found'}), 404)
    except Exception as e:
        return make_response(jsonify({'message': 'error getting user', 'error': str(e)}), 500)
    

# update a user
@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    try: 
        user = User.query.filter_by(id=id).first()
        if user:
            data = request.get_json()
            user.username = data['username']
            user.email = data['email']
            db.session.commit()
            return make_response(jsonify({'message': 'User updated'}), 200)
        return make_response(jsonify({'message': 'User not found'}), 404)
    except Exception as e:
        return make_response(jsonify({'message': 'error updating user', 'error': str(e)}), 500)
    

# delete a user
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    try: 
        user = User.query.filter_by(id=id).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            return make_response(jsonify({'message': 'User deleted'}), 200)
        return make_response(jsonify({'message': 'User not found'}), 404)
    except Exception as e:
        return make_response(jsonify({'message': 'error deleting user', 'error': str(e)}), 500)
    

if __name__ == '__main__':
    app.run(debug=True)