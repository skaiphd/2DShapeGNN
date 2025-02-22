import torch
from torch_geometric.loader import DataLoader
import matplotlib.pyplot as plt
from utils import load_config
from GNNModel import SimpleGNN
import random

class Evaluator:
    """
    Evaluates the trained GNN model on a dataset.
    
    Attributes:
        model (nn.Module): The trained GNN model.
        loader (DataLoader): DataLoader for the test dataset.
        device (torch.device): Device to perform evaluation (CPU or GPU).
    """
    def __init__(self, model, loader, device):
        self.model = model.to(device)
        self.loader = loader
        self.device = device

    def evaluate(self):
        """
        Evaluate the model and return predictions for all graphs.
        
        Returns:
            list: A list of tuples (graph_data, predicted_labels).
        """
        self.model.eval()
        predictions = []
        with torch.no_grad():
            for data in self.loader:
                data = data.to(self.device)
                pred = self.model(data.x, data.edge_index, data.batch).argmax(dim=1)
                predictions.append((data, pred))  # Store batch of predictions
        return predictions
    

class Visualizer:
    """
    Visualizes graphs and their predicted labels.
    """
    @staticmethod
    def plot_graph(data, pred, label_mapping):
        """
        Plot a graph with its predicted label.
        
        Args:
            data (torch_geometric.data.Data): The graph data.
            pred (torch.Tensor): Predicted label for the graph.
            label_mapping (dict): Mapping of label indices to their names.
        """
        nodes = data.x.cpu().numpy()  # Node positions
        edges = data.edge_index.cpu().numpy()  # Edge connectivity

        plt.figure(figsize=(6, 6))
        # Plot edges
        for edge in edges.T:
            start, end = edge
            plt.plot(
                [nodes[start, 0], nodes[end, 0]],
                [nodes[start, 1], nodes[end, 1]],
                color="gray",
                alpha=0.5,
            )
        # Plot nodes
        plt.scatter(nodes[:, 0], nodes[:, 1], color="blue", s=100, alpha=0.8)
        plt.title(f"Predicted: {label_mapping[pred.item()]}")
        plt.axis("equal")
        plt.show()

# Split data into train, validation, and test sets
def split_data(graphs, train_split, val_split):
    """
    Splits the dataset into training, validation, and test sets.
    
    Args:
        graphs (list): List of graphs.
        train_split (float): Fraction of data for training.
        val_split (float): Fraction of data for validation.
        
    Returns:
        tuple: Train, validation, and test datasets.
    """
    num_graphs = len(graphs)
    train_size = int(train_split * num_graphs)
    val_size = int(val_split * num_graphs)

    train_graphs = graphs[:train_size]
    val_graphs = graphs[train_size:train_size + val_size]
    test_graphs = graphs[train_size + val_size:]

    return train_graphs, val_graphs, test_graphs


if __name__ == "__main__":
    """
    Main script to evaluate the trained GNN model and visualize predictions.
    """
    # Load configuration
    config = load_config()

    # Load preprocessed graphs
    graphs = torch.load("processed_graphs.pt")
    train_graphs, val_graphs, test_graphs = split_data(
        graphs,
        train_split=config["data"]["train_split"],
        val_split=config["data"]["validation_split"]
    )

    # Create DataLoader for the test dataset
    test_loader = DataLoader(test_graphs, batch_size=config["training"]["batch_size"], shuffle=False)

    # Initialize model and load trained weights
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    model = SimpleGNN(
        input_dim=config["model"]["input_dim"],
        hidden_dim=config["model"]["hidden_dim"],
        output_dim=config["model"]["output_dim"],
        num_layers=config["model"]["num_layers"],
        dropout=config["model"]["dropout"]
    ).to(device)
    
    model.load_state_dict(torch.load("trained_model.pth"))
    model.eval()

    # Evaluate the model on the test set
    print("Evaluating the model...")
    evaluator = Evaluator(model, test_loader, device)
    predictions = evaluator.evaluate()

    # Visualize predictions
    label_mapping = {0: "triangle", 1: "rectangle", 2: "circle", 3: "hexagon", 4: "ellipse"}
    num_test_samples_to_plot = config["evaluation"]["num_test_samples_to_plot"]
    
    # Select random samples from test set to visualize
    random_samples = random.sample(predictions, num_test_samples_to_plot)
    
    print("Visualizing predictions...")
    visualizer = Visualizer()
    for data, preds in random_samples:  # Loop over randomly selected samples
        for graph_idx, pred in enumerate(preds):  # Loop over graphs in the batch
            visualizer.plot_graph(data[graph_idx], pred, label_mapping)
