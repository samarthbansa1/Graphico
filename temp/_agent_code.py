import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def generate_heatmap(file_path):
    try:
        # Load the CSV file into a pandas DataFrame
        df = pd.read_csv(file_path)

        # Check if necessary columns exist.  If not, use available ones
        if 'Fare' not in df.columns or 'Pclass' not in df.columns or 'Embarked' not in df.columns:
            print("Warning: One or more necessary columns ('Fare', 'Pclass', 'Embarked') are missing.")
            print("Available columns:", df.columns)
            # Choose suitable replacements.  Adapt this based on your actual data.
            if 'fare' in df.columns :
                df = df.rename(columns={'fare':'Fare'})
            if 'pclass' in df.columns:
                df = df.rename(columns={'pclass':'Pclass'})
            if 'embarked' in df.columns:
                 df = df.rename(columns={'embarked':'Embarked'})
            if 'Fare' not in df.columns or 'Pclass' not in df.columns or 'Embarked' not in df.columns:
                print("Error:  Couldn't find suitable replacements.  Visualization cannot be generated.")
                return

        # Calculate the mean Fare for each combination of Pclass and Embarked.
        mean_fare = df.groupby(['Pclass', 'Embarked'])['Fare'].mean().unstack()


        # Create the heatmap
        plt.figure(figsize=(10, 6))
        sns.heatmap(mean_fare, annot=True, cmap='viridis', fmt=".2f")
        plt.title('Mean Fare by Pclass and Embarked')
        plt.xlabel('Embarked')
        plt.ylabel('Pclass')
        plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
        plt.tight_layout()


        plt.savefig('output.png')
        plt.close()
        print("Heatmap generated successfully and saved as output.png")

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except KeyError as e:
        print(f"Error: Key error {e}.  Check column names in your data.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")




# Replace 'data.csv' with your actual file path
generate_heatmap('data.csv')