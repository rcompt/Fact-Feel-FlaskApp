using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

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

            //Invoke script
            ProcessStartInfo script = new ProcessStartInfo()
            {
                FileName = 
            };

            return retVal;
        }
    }
}
