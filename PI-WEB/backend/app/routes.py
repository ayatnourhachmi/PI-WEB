from flask import Blueprint, request, jsonify, render_template
from .utils import REGION_MAPPING, filter_data, calculate_averages, convert_currency_to_avg, predict_region  # Import functions from utils
import pandas as pd
import os

# Create Flask Blueprint
routes = Blueprint('routes', __name__)

@routes.route('/')
def home():
    """
    Root route to serve the index.html file.
    """
    return render_template('index.html')  # Ensure 'index.html' is in the templates folder

@routes.route('/display_results', methods=['POST'])
def display_results():
    """
    Flask route to handle region and family status requests.
    """
    try:
        # Get the JSON data from the request
        request_data = request.get_json()
        print(f"[INFO] Incoming request data: {request_data}")  # Log the incoming request
        
        # Extract region and family status from the request
        region_id = request_data.get('region')
        family_status = request_data.get('family_status', 'Married')  # Default to Married

        # Validate region ID
        if not region_id:
            print("[ERROR] Region ID is missing in the request.")
            return jsonify({"message": "Region ID is required."}), 400

        # Map region ID to region name
        region_name = REGION_MAPPING.get(int(region_id))
        if not region_name:
            print(f"[ERROR] Invalid region ID: {region_id}")
            return jsonify({"message": f"Invalid region ID: {region_id}."}), 400

        # Log the region name and family status for context
        print(f"[INFO] Processing for region: {region_name}, family status: {family_status}")

        import os

        # Resolve the path relative to the backend directory
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # Go up one level from app
        file_path = os.path.join(base_dir, 'data', 'updated_responses.xlsx')

        # Check if the file exists
        print("Resolved file path:", file_path)
        print("File exists:", os.path.exists(file_path))


        data = pd.read_excel(file_path)


        # Nettoyage et standardisation des colonnes
        data.columns = data.columns.str.strip()  # Supprime les espaces inutiles dans les noms de colonnes
        data['Family status'] = data['Situation Familiale'].replace({'Divorcé': 'Single','Célibataire': 'Single','Marié': 'Married','Celibataire': 'Single'})

        # Application de la fonction de conversion sur les colonnes numériques
        numeric_columns = ['Salaire (DH)', 'Perte Mensuelle Transport (DH)', 'Dépenses Alimentaires (DH)', 'Dépenses Par Repas (DH)']
        for col in numeric_columns:
            data[col] = data[col].apply(convert_currency_to_avg)

        # Gestion des valeurs manquantes dans les colonnes nécessaires pour le calcul
        required_columns = ['Factures Mensuelles (DH)', 'Perte Mensuelle Transport (DH)', 'Dépenses Alimentaires (DH)', 'Dépenses Par Repas (DH)']
        data[required_columns] = data[required_columns].fillna(0)  # Remplace les valeurs manquantes par 0

        # Création de la colonne "Dépense Mensuelle Totale"
        data['Dépense Mensuelle Totale'] = data[required_columns].sum(axis=1)  # Somme des dépenses mensuelles

        # Filter data using utility function
        filtered_data = filter_data(data,region_name, family_status)
        print(f"[INFO] Filtered data count: {len(filtered_data)}")  # Log the number of records found

        # Calculate averages using utility function
        averages = calculate_averages(filtered_data)

        # Handle case where no data is found
        if averages is None:
            print(f"[INFO] No data found for region: {region_name}, family status: {family_status}")
            return jsonify({
                "message": f"No data available for region '{region_name}' and family status '{family_status}'."
            }), 404

        # Successful response
        response_data = {
            "message": f"Results for region '{region_name}' and family status '{family_status}':",
            "averages": averages
        }
        print(f"[INFO] Response data: {response_data}")  # Log the response
        return jsonify(response_data)

    except Exception as e:
        # Log the exception for debugging
        print(f"[ERROR] Exception in /display_results: {e}")
        return jsonify({"message": "An internal server error occurred."}), 500

@routes.route('/display_results_byMiniForm', methods=['GET'])
def display_results_byMiniForm():
    """Route to predict the region based on salary and family status."""
    try:
        # Retrieve inputs from the request
        salary = request.args.get('salary', type=float)
        family_status = request.args.get('family_status', type=str)

        # Validate inputs
        if salary is None:
            return jsonify({"error": "Invalid input: Salary is required and must be a number."}), 400

        if family_status not in ['Single', 'Married']:
            return jsonify({"error": "Invalid input: Family status must be 'Single' or 'Married'."}), 400

        # Call the prediction function
        region = predict_region(salary, family_status)

        # Return the predicted region
        return jsonify({
            "salary": salary,
            "family_status": family_status,
            "predicted_region": region
        }), 200

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500