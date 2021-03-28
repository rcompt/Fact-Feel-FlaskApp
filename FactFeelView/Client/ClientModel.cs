using FactFeelUI.Resources;
using FactFeelUI.Utilities;
using System;

namespace FactFeelUI.Client
{
    /// <summary>
    /// Wrapper for client python script
    /// </summary>
    public class ClientModel
    {
        public ClientModel()
        {

        }

        public EventHandler<ClientEventArgs> ClientUpdated;
        public void OnClientUpdated(object sender, ClientEventArgs e)
        {
            ClientUpdated?.Invoke(sender, e);
        }

        public bool Listen()
        {
            bool retVal = false;

            PythonWrapper.InvokeScript(Settings.Default.ConfigFileLocation, ""); //TODO: Fill out

            return retVal;
        }
    }
}
