using FactFeelUI.Client;
using FactFeelUI.Resources;
using Newtonsoft.Json;
using System.IO;
using FactFeelUI.Utilities;

namespace FactFeelUI
{
    public class FactFeelViewModel : ObservableBase
    {
        public FactFeelConfig Config;

        public FactFeelViewModel()
        {
            ParseConfig(ref Config);

            int numberOfLights = 3;
            clientVm = new ClientViewModel(numberOfLights);
        }

        private ClientViewModel clientVm = null;
        public ClientViewModel ClientVm
        {
            get
            {
                return clientVm;
            }
            set
            {
                SetProperty(ref clientVm, value);
            }
        }

        private void ParseConfig(ref FactFeelConfig config)
        {
            string jsonString = File.ReadAllText(Settings.Default.ConfigFileLocation);
            config = JsonConvert.DeserializeObject<FactFeelConfig>(jsonString);
        }
    }
}
