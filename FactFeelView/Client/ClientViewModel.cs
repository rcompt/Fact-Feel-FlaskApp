using FactFeelUI.Utilities;
using System;
using LiveCharts;
using System.Windows.Media;
using System.Collections.ObjectModel;

namespace FactFeelUI.Client
{
    public class ClientViewModel : ObservableBase
    {
        private readonly int NumberOfLights;

        public ClientViewModel(int numberOfLights)
        {
            //TODO: Figure out if it's possible to query state of script any time
            //      - CurrentTextSequence
            //      - IsRecording
            //      - ErrorState

            NumberOfLights = numberOfLights;

            lightList = new ObservableCollection<Brush>();
            for (int i = 0; i < numberOfLights; i++)
            {
                lightList.Add(Brushes.Transparent);
            }
        }

        //TOOD: need specifics on display axes
        private SeriesCollection outputData = null; //TODO: rename. The UML calls this "Timeseries of outputs"
        public SeriesCollection OutputData
        {
            get
            {
                if (outputData == null)
                {
                    outputData = new SeriesCollection();
                }

                return outputData;
            }
        }

        private double sequenceSuccessRate = 0;
        public double SequenceSuccessRate
        {
            get
            {
                return sequenceSuccessRate;
            }
            set
            {
                SetProperty(ref sequenceSuccessRate, value);
            }
        }

        ObservableCollection<Brush> lightList = null;
        ObservableCollection<Brush> LightList
        {
            get
            {
                return lightList;
            }
            set
            {
                SetProperty(ref lightList, value);
            }
        }

        private string currentRecognizedText = string.Empty;
        public string CurrentRecognizedText
        {
            get
            {
                return currentRecognizedText;
            }
            set
            {
                SetProperty(ref currentRecognizedText, value);
            }
        }

        private int currentSequenceID = 0;
        public int CurrentSequenceID
        {
            get
            {
                return currentSequenceID;
            }
            set
            {
                SetProperty(ref currentSequenceID, value);
            }
        }

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

        private double CalculateSuccessRate()
        {
            throw new NotImplementedException();
        }
    }
}
