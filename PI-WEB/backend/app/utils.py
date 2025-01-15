import pandas as pd
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
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


def convert_currency_to_avg_QDA(value):
    """
    Convert monetary values into floating-point averages.
    Handles ranges (e.g., "500-1000") and non-numeric characters (e.g., "500dh").
    """
    if isinstance(value, str):
        value = value.lower().replace('dh', '').strip()
        if '-' in value:  # Handle ranges like "0-2500"
            low, high = map(float, value.split('-'))
            return (low + high) / 2
        try:
            return float(value)
        except ValueError:
            return 0.0  # Default to 0.0 if conversion fails
    return value

def clean_family_status_QDA(family_status):
    """
    Normalize family status into consistent categories.
    """
    mapping = {
        'Marié': 'Married',
        'Mariée': 'Married',
        'Célibataire': 'Single',
        'Divorcé': 'Single',
        'Divorcée': 'Single',
        'Single': 'Single',
        'Married': 'Married'
    }
    result = mapping.get(family_status.strip(), None)
    if result is None:
        raise ValueError(f"Invalid family status: {family_status}. Must be 'Single' or 'Married'.")
    return result

def predict_region(salaire, family_status):
    """
    Predict the most suitable region based on salary and family status.
    Randomly selects a region weighted by probabilities.
    """
    try:
        # Load the dataset
        data = pd.read_excel('Balanced_Situation_Familiale_Data.xlsx')

        # Preprocess the dataset
        data['Situation Familiale'] = data['Situation Familiale'].apply(clean_family_status_QDA)
        family_status = clean_family_status_QDA(family_status)  # Clean input as well
        data['Salaire (DH)'] = data['Salaire (DH)'].apply(convert_currency_to_avg_QDA)

        # Drop rows with missing essential values
        data = data.dropna(subset=['Salaire (DH)', 'Région', 'Situation Familiale'])

        # Encode categorical family status
        label_encoder = LabelEncoder()
        data['Family Status Encoded'] = label_encoder.fit_transform(data['Situation Familiale'])

        # Prepare features and target
        features = data[['Salaire (DH)', 'Family Status Encoded']]
        target = data['Région']

        # Balance the dataset
        majority_class = data['Région'].value_counts().idxmax()
        max_count = data['Région'].value_counts().max()
        data_balanced = data.copy()

        for region in data['Région'].unique():
            region_data = data[data['Région'] == region]
            if len(region_data) < max_count:
                region_data_upsampled = resample(region_data, replace=True, n_samples=max_count, random_state=42)
                data_balanced = pd.concat([data_balanced, region_data_upsampled])

        # Scale features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(data_balanced[['Salaire (DH)', 'Family Status Encoded']])

        # Split data into train and test sets
        X_train, X_test, y_train, y_test = train_test_split(features_scaled, data_balanced['Région'], test_size=0.3, random_state=42)

        # Train the QDA model
        qda = QuadraticDiscriminantAnalysis(reg_param=0.1)
        qda.fit(X_train, y_train)

        # Encode the input family status
        family_status_encoded = label_encoder.transform([family_status])[0]

        # Predict probabilities for the input
        input_data = scaler.transform([[salaire, family_status_encoded]])
        probabilities = qda.predict_proba(input_data)[0]

        # Randomly select a region weighted by probabilities
        regions = qda.classes_
        predicted_region = random.choices(regions, weights=probabilities, k=1)[0]

        return predicted_region

    except ValueError as ve:
        print(f"[ERROR] {str(ve)}")
        raise
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


def predict_expenses(model, salary, region, family_status, target_percentage, spending_preferences):
    """
    Predicts expenses for each category and adjusts them to meet the user's target remaining balance
    and spending preferences.

    Args:
        model: Trained model pipeline for predicting expenses.
        salary: User's monthly salary (in DH).
        region: User's region as a string.
        family_status: User's family status (Single/Married).
        target_percentage: Percentage of salary the user wants to save as remaining balance.
        spending_preferences: Array of spending preference weights (1.5 for High, 1.0 for Medium, 0.5 for Low).

    Returns:
        adjusted_expenses: Array of adjusted predicted expenses for each category.
        final_remaining_balance: Remaining balance after adjusting expenses.
    """
    # Encode user inputs as a DataFrame
    input_data = pd.DataFrame({
        'Salaire (DH)': [salary],
        'Région': [region],
        'Family status': [family_status]
    })

    # Predict expenses using the trained model
    predicted_expenses = model.predict(input_data)[0]  # Returns a single row of predictions

    # Apply user-defined spending preferences to the predicted expenses
    adjusted_expenses = predicted_expenses * spending_preferences

    # Calculate the total predicted expenses and the user's target remaining balance
    total_expenses = sum(adjusted_expenses)
    target_remaining_balance = salary * (target_percentage / 100)
    max_expenses = salary - target_remaining_balance

    # Adjust expenses proportionally if they exceed the allowable budget
    if total_expenses > max_expenses:
        adjustment_factor = max_expenses / total_expenses
        adjusted_expenses = adjusted_expenses * adjustment_factor

    # Calculate the final remaining balance after expenses
    final_remaining_balance = salary - sum(adjusted_expenses)

    # Return adjusted expenses and final remaining balance
    return adjusted_expenses, final_remaining_balance

def setup_model(file_path='./data/updated_responses.xlsx'):
    """
    Loads the dataset, preprocesses it, and trains the model.

    Args:
        file_path: Path to the dataset file.

    Returns:
        A trained machine learning model pipeline, or None if an error occurs.
    """
    try:
        # Load the dataset
        data = pd.read_excel('./data/updated_responses.xlsx')

        if data is None:
            raise ValueError("Failed to load data. Check the file path or data format.")

        # Preprocess the dataset
        processed_data = preprocess_data(data)

        # Train the model
        model = train_model(processed_data)

        return model
    except Exception as e:
        print(f"Error setting up the model: {e}")
        return None

def train_model(data):
    """
    Trains a Linear Regression model to predict expenses based on user inputs.
    """
    # Features and target
    X = data[['Salaire (DH)', 'Région', 'Family status']]
    y = data[['Loyer (DH)', 'Factures Mensuelles (DH)', 'Perte Mensuelle Transport (DH)', 'Dépenses Alimentaires (DH)']]

    # Preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), ['Salaire (DH)']),
            ('cat', OneHotEncoder(), ['Région', 'Family status'])
        ]
    )

    # Regression model
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', LinearRegression())
    ])

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train the model
    model.fit(X_train, y_train)

    return model


def preprocess_data(data):
    """
    Preprocesses the dataset by handling non-numeric values, encoding categorical variables,
    and normalizing numerical features.
    """
    # Handle non-numeric values in relevant columns
    def convert_to_numeric(value):
        """
        Converts a string value with ranges or non-numeric characters into a numeric value.
        Handles cases like '5000-10000DH', 'Moins de 500 dh', 'Plus de 2500 dh', '0 dh'.
        """
        if isinstance(value, str):
            value = value.lower().replace('dh', '').strip()  # Remove 'DH' and extra spaces
            if 'plus de' in value:
                return float(value.replace('plus de', '').strip())
            elif 'moins de' in value:
                return float(value.replace('moins de', '').strip())
            elif '-' in value:  # Handle ranges like '5000-10000'
                low, high = map(float, value.split('-'))
                return (low + high) / 2
            try:
                return float(value)  # Convert to float if possible
            except ValueError:
                return np.nan  # Return NaN if conversion fails
        return value  # Return the value as is if it's already numeric

    # Apply the conversion function to relevant columns
    columns_to_convert = ['Salaire (DH)', 'Factures Mensuelles (DH)', 'Dépenses Alimentaires (DH)',
                          'Loyer (DH)', 'Perte Mensuelle Transport (DH)']  # Add other relevant columns
    for col in columns_to_convert:
        data[col] = data[col].apply(convert_to_numeric)

    # Handle missing values (e.g., replace NaN with 0 or column mean)
    data.fillna(0, inplace=True)

    # Encode categorical variables
    data['Family status'] = data['Situation Familiale'].replace({
        'Divorcé': 'Single', 'Célibataire': 'Single', 'Marié': 'Married', 'Celibataire': 'Single'
    })

    return data
