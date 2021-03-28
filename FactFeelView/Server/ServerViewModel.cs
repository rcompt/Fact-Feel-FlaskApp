using FactFeelUI.Utilities;

namespace FactFeelUI.Server
{
    public class ServerViewModel : ObservableBase
    {
        public ServerViewModel()
        {
            //TODO: Figure out if it's possible to query state of script any time
            //      - IsProcessing
            //      - IsVectorizing
            //      - ErrorState
        }

        //TODO: want this here or just client side?
        private double currentPrediction = 0;
        public double CurrentPrediction
        {
            get
            {
                return currentPrediction;
            }
            set
            {
                SetProperty(ref currentPrediction, value);
            }
        }
    }
}
