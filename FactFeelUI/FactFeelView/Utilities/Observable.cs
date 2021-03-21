using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading.Tasks;

namespace FactFeelMainView.Utilities
{
    /// <summary>
    /// Used to handle the on property change value of any property that inherits from this class.
    /// This class should be primarily used for viewmodel inheritance. 
    /// </summary>
    public abstract class AObservable : INotifyPropertyChanged
    {
        private readonly Object observableLock = new Object();


        #region INotifyPropertyChanged Interface
        /// <summary>
        /// Method used to handle the INotifyPropertyChanged event.
        /// </summary>
        public event PropertyChangedEventHandler PropertyChanged;
        #endregion INotifyPropertyChanged Interface

        #region Methods
        /// <summary>
        /// Invokes the property changed event.
        /// </summary>
        /// <param name="name"></param>
        public virtual void OnPropertyChanged([CallerMemberName] String name = "")
        {
            lock (observableLock)
            {
                this.VerifyPropertyName(name);
                PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
            }
        }

        /// <summary>
        /// Invokes the Property Changed event if the values passed in do not match.
        /// </summary>
        /// <example>
        ///     public T Property
        ///     {
        ///         get { return _property; }
        ///         set { SetProperty(ref _property, value);
        ///     }
        /// </example>
        /// <typeparam name="T"></typeparam>
        /// <param name="property">Reference to the private variable to be set</param>
        /// <param name="value">Value that the property will be set to</param>
        /// <param name="name">Public properties exact name</param>
        public virtual void SetProperty<T>(ref T property, T value, [CallerMemberName] String name = "")
        {
            lock (observableLock)
            {
                this.VerifyPropertyName(name);

                if (!EqualityComparer<T>.Default.Equals(property, value))
                {
                    property = value;
                    PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
                }
            }
        }
        #endregion Methods

        #region Debug
        /// <summary>
        /// Warns the developer if this object does not havea public property with the specified name. This
        /// method does not exist in a Release build.
        /// </summary>
        /// <param name="propertyName"></param>
        [Conditional("DEBUG")]
        [DebuggerStepThrough]
        public virtual void VerifyPropertyName(String propertyName)
        {
            // Verify that the property name matches a real,
            // public, instance property on this object.
            if (TypeDescriptor.GetProperties(this)[propertyName] == null)
            {
                throw new ArgumentException("Invalid property name: " + propertyName);
            }
        }
        #endregion Debug
    }


    /// <summary>
    /// Generic version of AObservable. This can be used to have Lists of observable generics
    /// that will not throw an OnProperty changed for an entire collection but just the single
    /// index. 
    /// </summary>
    /// <typeparam name="T"></typeparam>
    /// <seealso cref="AObservable"/>
    public class Observable<T> : AObservable
    {
        private T _property;
        /// <summary>
        /// Stored variable that is being observed.
        /// </summary>
        public T Property
        {
            get { return _property; }
            set { SetProperty(ref _property, value); }
        }
    }

    public class ObservableBase : AObservable
    {

    }
}
