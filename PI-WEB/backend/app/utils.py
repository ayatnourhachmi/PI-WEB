import pandas as pd
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import numpy as np

# Region mapping (ID to Name)
REGION_MAPPING = {
    1: "Tanger-Tétouan-Al Hoceima",
    2: "L’Oriental",
    3: "Fès-Meknès",
    4: "Rabat-Salé-Kénitra",
    5: "Béni Mellal-Khénifra",
    6: "Casablanca-Settat",
    7: "Marrakech-Safi",
    8: "Drâa-Tafilalet",
    9: "Souss-Massa",
    10: "Guelmim-Oued Noun",
    11: "Laâyoune-Sakia Al Hamra",
    12: "Dakhla-Oued Eddahab",
}

def clean_family_status(family_status):
    mapping = {
        'Marié': 'Married',
        'Mariée': 'Married',
        'Célibataire': 'Single',
        'Divorcé': 'Single',
        'Divorcée': 'Single'
    }
    return mapping.get(family_status.strip().title(), 'Other')  # Default to 'Other'



def predict_region(salaire, family_status):

    """
    Predict the most suitable region based on salary and family status.
    """
    try:
        # Load the dataset
        data = pd.read_excel('./data/updated_responses.xlsx')

        # Debug: Print column names
        print("Columns in the dataset:", data.columns.tolist())

        # Ensure the necessary columns exist
        required_columns = ['Salaire (DH)', 'Région', 'Situation Familiale']
        for col in required_columns:
            if col not in data.columns:
                raise ValueError(f"Missing required column: {col}")

        # Debug: Check for missing values
        print("Missing values in required columns:", data[required_columns].isnull().sum())

        # Handle missing values
        data = data.dropna(subset=required_columns)

        # Clean the 'Situation Familiale' column
        data['Situation Familiale'] = data['Situation Familiale'].apply(clean_family_status)

        # Normalize input for family status
        family_status = clean_family_status(family_status)  # Clean the input as well

        # Convert salary to numeric
        data['Salaire (DH)'] = data['Salaire (DH)'].apply(convert_currency_to_avg)

        # Encode categorical family status
        label_encoder = LabelEncoder()
        data['Family Status Encoded'] = label_encoder.fit_transform(data['Situation Familiale'])

        # Prepare features and target
        features = data[['Salaire (DH)', 'Family Status Encoded']]
        target = data['Région']

        print(data.head())  # Debug: Print the first few rows after cleaning

        # Split data into train and test sets
        X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.3, random_state=42)

        # Train a QDA model
        qda = QuadraticDiscriminantAnalysis()
        qda.fit(X_train, y_train)

        # Encode the input family status
        family_status_encoded = label_encoder.transform([family_status])[0]

        # Predict the region
        input_data = np.array([[salaire, family_status_encoded]])
        predicted_region = qda.predict(input_data)

        return predicted_region[0]

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        raise

# Fonction pour convertir les valeurs monétaires en moyenne (gestion des plages de valeurs et des caractères non numériques)
def convert_currency_to_avg(value):
    """
    Convertit une valeur monétaire en un nombre flottant.
    Gère les plages de valeurs (ex: "500-1000"), les caractères non numériques (ex: "500dh"), et les valeurs manquantes.
    """
    if isinstance(value, str):
        value = value.lower().replace('dh', '').strip()  # Supprime "dh" et les espaces inutiles
        if 'plus de' in value:
            return float(value.replace('plus de', '').strip())
        elif 'moins de' in value:
            return float(value.replace('moins de', '').strip())
        if '-' in value:  # Gère les plages de valeurs comme "500-1000"
            low, high = map(float, value.split('-'))
            return (low + high) / 2
        try:
            return float(value)  # Convertit en float si possible
        except ValueError:
            return 0.0  # Retourne 0.0 si la conversion échoue
    return value  # Retourne la valeur d'origine si ce n'est pas une chaîne

# Function to filter data
def filter_data(data, region, family_status):
    """
    Filters the data based on the region and family status.
    """
    filtered_data = data[(data['Région'] == region) & (data['Family status'] == family_status)]
    return filtered_data

# Function to calculate averages
def calculate_averages(filtered_data):
    """
    Calculates averages for the relevant columns.
    """
    if filtered_data.empty:
        return None

    averages = {
        'Average Rent (DH)': filtered_data['Loyer (DH)'].mean(),
        'Average Monthly Bills (DH)': filtered_data['Factures Mensuelles (DH)'].mean(),
        'Average Transport Loss (DH)': filtered_data['Perte Mensuelle Transport (DH)'].mean(),
        'Average Food Expenses (DH)': filtered_data['Dépenses Alimentaires (DH)'].mean(),
        'Average Total Monthly Expenses (DH)': filtered_data['Dépense Mensuelle Totale'].mean()
    }

    return averages