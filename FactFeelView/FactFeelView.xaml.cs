using System.Windows;

namespace FactFeelUI
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class FactFeelView : Window
    {
        public FactFeelView()
        {
            InitializeComponent();
            DataContext = new FactFeelViewModel();
        }
    }
}
