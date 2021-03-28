using FactFeelUI.Client;
using FactFeelUI.Resources;
using FactFeelUI.Server;
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
            //TODO: Create config that keeps track of info:
            //      - Number of physical lights hooked up
            //      - other stuff
            ParseConfig(ref Config);

            //TODO: Could also prompt the user to enter info at startup:
            //      - How many lights do you have?
            //      - Microphone or digital audio out?

            int numberOfLights = 3;
            clientVm = new ClientViewModel(numberOfLights);

            serverVm = new ServerViewModel();
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

        private ServerViewModel serverVm = null;
        public ServerViewModel ServerVm
        {
            get
            {
                return serverVm;
            }
            set
            {
                SetProperty(ref serverVm, value);
            }
        }

        private void ParseConfig(ref FactFeelConfig config)
        {
            string jsonString = File.ReadAllText(Settings.Default.ConfigFileLocation);
            config = JsonConvert.DeserializeObject<FactFeelConfig>(jsonString);
        }
    }
}
