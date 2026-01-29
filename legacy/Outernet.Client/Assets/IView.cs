namespace Outernet.Client
{
    public interface IView
    {
        void AddBinding(ViewBinding binding);
        void RemoveBinding(ViewBinding binding);

        void Teardown();
    }
}