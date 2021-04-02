using Avalonia;
using Avalonia.Controls;
using Avalonia.Markup.Xaml;

namespace FactFeelUI.Client
{
    public class ClientView : UserControl
    {
        public ClientView()
        {
            InitializeComponent();
        }

        private void InitializeComponent()
        {
            AvaloniaXamlLoader.Load(this);
        }
    }
}
